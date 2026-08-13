import calendar
import datetime
from decimal import Decimal
from django.db import models as db_models
from django.utils import timezone
from apps.attendance.models import Attendance, Holiday
from apps.leave.models import LeaveRequest
from apps.payroll.models import PayrollPolicy, SalaryStructure
from apps.attendance.utils import is_working_day
from apps.conveyance.models import Conveyance

def calculate_payroll_deductions(student_profile, month_date):
    """
    Auto-calculates the base_stipend, conveyances, and deductions for a given student and month.
    """
    # 1. Fetch configurations
    try:
        salary_structure = student_profile.salary_structure
        base_stipend = float(salary_structure.base_stipend)
    except SalaryStructure.DoesNotExist:
        base_stipend = 0.0

    # 2. Get date ranges
    year = month_date.year
    month = month_date.month
    
    # Get number of days in month
    _, num_days = calendar.monthrange(year, month)
    
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)
    
    # Do not evaluate beyond today if the month is the current month
    today = timezone.now().date()
    evaluation_end_date = min(end_date, today) if start_date.month == today.month else end_date

    # 3. Gather data
    attendances_dict = {
        a.date: a for a in Attendance.objects.filter(student=student_profile, date__range=[start_date, evaluation_end_date])
    }
    
    approved_leaves = LeaveRequest.objects.filter(
        student=student_profile, 
        status__in=['Manager Approved', 'Principal Approved'],
        start_date__lte=evaluation_end_date,
        end_date__gte=start_date
    )
    
    approved_conveyances = Conveyance.objects.filter(
        student=student_profile,
        status='Approved',
        date__range=[start_date, end_date]
    )
    total_conveyance = sum(float(c.total_amount) for c in approved_conveyances)

    def is_on_leave(d):
        for l in approved_leaves:
            if l.start_date <= d <= l.end_date:
                return True
        return False
        
    def was_absent_on_working_day(d):
        if not is_working_day(d):
            return False
        if is_on_leave(d):
            return False
        # If no attendance record, or status is Absent
        if d not in attendances_dict:
            return True
        if attendances_dict[d].status == 'Absent':
            return True
        return False

    unapproved_leave_days = 0
    sandwich_penalty_days = 0
    late_count = 0
    
    current = start_date
    while current <= evaluation_end_date:
        if is_working_day(current):
            # Normal working day
            if was_absent_on_working_day(current):
                unapproved_leave_days += 1
            elif current in attendances_dict and attendances_dict[current].status == 'Late':
                late_count += 1
                
        else:
            # Holiday or Weekend
            # Sandwich logic: Absent before OR absent after means deduction for the holiday
            prev_working = current - datetime.timedelta(days=1)
            while prev_working >= start_date and not is_working_day(prev_working):
                prev_working -= datetime.timedelta(days=1)
                
            next_working = current + datetime.timedelta(days=1)
            while next_working <= evaluation_end_date and not is_working_day(next_working):
                next_working += datetime.timedelta(days=1)
                
            absent_before = False
            absent_after = False
            
            if prev_working >= start_date and was_absent_on_working_day(prev_working):
                absent_before = True
                
            if next_working <= evaluation_end_date and was_absent_on_working_day(next_working):
                absent_after = True
                
            if absent_before or absent_after:
                sandwich_penalty_days += 1
                    
        current += datetime.timedelta(days=1)
        
    # Calculate Late penalty based on new rule:
    # 3 lates = 1 day, 5 lates = 2 days, 7 lates = 3 days, etc.
    # Formula: 1 + (late_count - 3) // 2
    late_penalty_days = 0
    if late_count >= 3:
        late_penalty_days = 1 + (late_count - 3) // 2

    # 4. Calculate amounts based on FIXED 30-day month
    per_day_salary = base_stipend / 30 if base_stipend > 0 else 0
    
    leave_deduction = (unapproved_leave_days + sandwich_penalty_days) * per_day_salary
    late_deduction = late_penalty_days * per_day_salary
    
    return {
        'base_stipend': round(base_stipend, 2),
        'total_conveyance': round(total_conveyance, 2),
        'unapproved_leave_days': unapproved_leave_days,
        'sandwich_penalty_days': sandwich_penalty_days,
        'late_penalty_days': late_penalty_days,
        'leave_deduction': round(leave_deduction, 2),
        'late_deduction': round(late_deduction, 2),
    }


def generate_daily_payroll_log(student_profile, target_date):
    """
    Creates or updates a DailyPayrollLog for a specific student and date.
    This is called daily by the auto_generate_payroll command.
    """
    from apps.payroll.models import DailyPayrollLog
    
    # 1. Get salary structure
    try:
        salary_structure = student_profile.salary_structure
        base_stipend = float(salary_structure.base_stipend)
    except SalaryStructure.DoesNotExist:
        base_stipend = 0.0
    
    per_day_salary = round(base_stipend / 30, 2) if base_stipend > 0 else 0
    
    # 2. Determine if it's a working day
    working_day = is_working_day(target_date)
    
    # 3. Get attendance for this day
    attendance = Attendance.objects.filter(student=student_profile, date=target_date).first()
    
    # 4. Check approved leave
    approved_leave = LeaveRequest.objects.filter(
        student=student_profile,
        status__in=['Manager Approved', 'Principal Approved'],
        start_date__lte=target_date,
        end_date__gte=target_date
    ).exists()
    
    # 5. Get conveyance for this day
    daily_conveyance = float(
        Conveyance.objects.filter(
            student=student_profile,
            status='Approved',
            date=target_date
        ).aggregate(total=db_models.Sum('total_amount'))['total'] or 0
    )
    
    # 6. Determine attendance status and daily salary
    att_status = 'N/A'
    day_salary = per_day_salary
    leave_ded = 0
    sandwich_ded = 0
    
    if not working_day:
        # Weekend or Holiday
        is_weekend = target_date.weekday() in [4, 5]  # Friday, Saturday
        att_status = 'Weekend' if is_weekend else 'Holiday'
        day_salary = per_day_salary  # Default: get salary for holidays/weekends
        
        # Sandwich rule check
        month_start = datetime.date(target_date.year, target_date.month, 1)
        _, num_days = calendar.monthrange(target_date.year, target_date.month)
        month_end = datetime.date(target_date.year, target_date.month, num_days)
        today = timezone.now().date()
        eval_end = min(month_end, today)
        
        # Find previous working day
        prev_working = target_date - datetime.timedelta(days=1)
        while prev_working >= month_start and not is_working_day(prev_working):
            prev_working -= datetime.timedelta(days=1)
        
        # Find next working day
        next_working = target_date + datetime.timedelta(days=1)
        while next_working <= eval_end and not is_working_day(next_working):
            next_working += datetime.timedelta(days=1)
        
        absent_before = False
        absent_after = False
        
        if prev_working >= month_start:
            absent_before = _is_absent_on_working_day(student_profile, prev_working)
        
        if next_working <= eval_end:
            absent_after = _is_absent_on_working_day(student_profile, next_working)
        
        if absent_before or absent_after:
            att_status = 'Sandwich'
            day_salary = 0
            sandwich_ded = per_day_salary
    else:
        # Working day
        if approved_leave:
            att_status = 'Leave'
            day_salary = per_day_salary  # Approved leave = paid
        elif attendance is None:
            # No attendance record = Absent (if date is today or past)
            if target_date <= timezone.now().date():
                att_status = 'Absent'
                day_salary = 0
                leave_ded = per_day_salary
            else:
                att_status = 'N/A'
                day_salary = per_day_salary
        elif attendance.status == 'Absent':
            att_status = 'Absent'
            day_salary = 0
            leave_ded = per_day_salary
        elif attendance.status == 'Late':
            att_status = 'Late'
            day_salary = per_day_salary  # Late deduction calculated accumulatively
        elif attendance.status == 'Half Day':
            att_status = 'Half Day'
            day_salary = per_day_salary  # Half day treated like late for now
        elif attendance.status == 'Present':
            att_status = 'Present'
            day_salary = per_day_salary
        elif attendance.status == 'Leave':
            att_status = 'Leave'
            day_salary = per_day_salary
        elif attendance.status == 'Holiday':
            att_status = 'Holiday'
            day_salary = per_day_salary
        else:
            att_status = attendance.status
            day_salary = per_day_salary
    
    # 7. Create or update DailyPayrollLog
    log, created = DailyPayrollLog.objects.update_or_create(
        student=student_profile,
        date=target_date,
        defaults={
            'per_day_salary': day_salary,
            'daily_conveyance': daily_conveyance,
            'attendance_status': att_status,
            'is_working_day': working_day,
            'late_deduction': 0,  # Will be recalculated at monthly level
            'leave_deduction': leave_ded,
            'sandwich_deduction': sandwich_ded,
        }
    )
    
    return log


def _is_absent_on_working_day(student_profile, target_date):
    """Helper: checks if a student was absent on a working day (no approved leave, no attendance)."""
    if not is_working_day(target_date):
        return False
    
    # Check approved leave
    approved_leave = LeaveRequest.objects.filter(
        student=student_profile,
        status__in=['Manager Approved', 'Principal Approved'],
        start_date__lte=target_date,
        end_date__gte=target_date
    ).exists()
    if approved_leave:
        return False
    
    attendance = Attendance.objects.filter(student=student_profile, date=target_date).first()
    if attendance is None:
        return True
    if attendance.status == 'Absent':
        return True
    return False


def recalculate_monthly_payroll(student_profile, month_date):
    """
    Aggregates all DailyPayrollLog entries for the month and updates the monthly PayrollRecord.
    Also recalculates late penalty deductions based on accumulated late count.
    """
    from apps.payroll.models import DailyPayrollLog, PayrollRecord
    
    year = month_date.year
    month = month_date.month
    _, num_days = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)
    
    # Get all daily logs for this month
    daily_logs = DailyPayrollLog.objects.filter(
        student=student_profile,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    if not daily_logs.exists():
        return None
    
    # Get salary structure
    try:
        salary_structure = student_profile.salary_structure
        base_stipend = Decimal(str(salary_structure.base_stipend))
    except SalaryStructure.DoesNotExist:
        base_stipend = Decimal('0.00')
    
    per_day_salary = (base_stipend / Decimal('30')).quantize(Decimal('0.01')) if base_stipend > 0 else Decimal('0.00')
    
    # Count late days for the month and calculate penalty
    late_count = daily_logs.filter(attendance_status='Late').count()
    late_penalty_days = 0
    if late_count >= 3:
        late_penalty_days = 1 + (late_count - 3) // 2
    
    total_late_deduction = (Decimal(str(late_penalty_days)) * per_day_salary).quantize(Decimal('0.01'))
    
    # Distribute late deduction to the latest late-day logs
    # First reset all late deductions
    daily_logs.update(late_deduction=0)
    
    if late_penalty_days > 0:
        # Assign late deduction to the last late-day log entry
        late_logs = list(daily_logs.filter(attendance_status='Late').order_by('-date'))
        if late_logs:
            last_late_log = late_logs[0]
            last_late_log.late_deduction = total_late_deduction
            last_late_log.save()
    
    # Re-fetch after updates to recalculate daily_net in logs
    daily_logs = DailyPayrollLog.objects.filter(
        student=student_profile,
        date__range=[start_date, end_date]
    )
    
    # Aggregate totals
    from django.db.models import Sum
    totals = daily_logs.aggregate(
        total_salary=Sum('per_day_salary'),
        total_conveyance=Sum('daily_conveyance'),
        total_late_deduction=Sum('late_deduction'),
        total_leave_deduction=Sum('leave_deduction'),
        total_sandwich_deduction=Sum('sandwich_deduction'),
        total_net=Sum('daily_net'),
    )
    
    total_leave_ded = Decimal(str(totals['total_leave_deduction'] or 0)) + Decimal(str(totals['total_sandwich_deduction'] or 0))
    total_late_ded = Decimal(str(totals['total_late_deduction'] or 0))
    total_conveyance = Decimal(str(totals['total_conveyance'] or 0))
    
    # Get or create monthly PayrollRecord
    payroll, created = PayrollRecord.objects.get_or_create(
        student=student_profile,
        month=start_date,
        defaults={
            'base_stipend': base_stipend,
            'status': 'Draft'
        }
    )
    
    # Don't modify if already Paid
    if payroll.status == 'Paid':
        return payroll
    
    # Update fields
    payroll.base_stipend = base_stipend
    payroll.conveyance_allowance = total_conveyance
    payroll.leave_deduction = total_leave_ded
    payroll.late_deduction = total_late_ded
    # bonus and other_deduction are left as-is (manager may have set them manually)
    
    # Check if last day of month -- finalize
    today = timezone.now().date()
    if today.day == num_days and today.month == month and today.year == year:
        if payroll.status == 'Draft':
            payroll.status = 'Generated'
    
    payroll.save()  # net_pay is auto-calculated in PayrollRecord.save()
    return payroll


