import calendar
import datetime
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
