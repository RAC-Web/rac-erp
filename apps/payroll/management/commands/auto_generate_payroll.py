import datetime
import calendar
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.students.models import StudentProfile
from apps.payroll.models import PayrollRecord
from apps.payroll.utils import calculate_payroll_deductions

class Command(BaseCommand):
    help = 'Automatically generates or updates payroll records for the current month.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        first_day_of_month = datetime.date(today.year, today.month, 1)
        
        # Check if today is the last day of the month
        _, last_day = calendar.monthrange(today.year, today.month)
        is_last_day = (today.day == last_day)

        students = StudentProfile.objects.filter(status='Active')
        count_updated = 0
        count_finalized = 0

        for student in students:
            # Only process if they have a salary structure
            if not hasattr(student, 'salary_structure'):
                continue

            # Get or create the payroll record for the current month
            payroll, created = PayrollRecord.objects.get_or_create(
                student=student,
                month=first_day_of_month,
                defaults={
                    'base_stipend': student.salary_structure.base_stipend,
                    'status': 'Draft'
                }
            )

            # If it's already Paid, do not alter it automatically
            if payroll.status == 'Paid':
                continue
            
            # Re-calculate based on current attendance/leave/conveyance
            data = calculate_payroll_deductions(student, first_day_of_month)
            
            # Update fields
            payroll.base_stipend = data['base_stipend']
            payroll.conveyance_allowance = data['total_conveyance']
            # We don't overwrite bonus and other_deduction as the manager might have set them manually
            payroll.leave_deduction = data['leave_deduction']
            payroll.late_deduction = data['late_deduction']
            
            # On the last day of the month, finalize the payroll to 'Generated'
            if is_last_day and payroll.status == 'Draft':
                payroll.status = 'Generated'
                count_finalized += 1
            
            # Note: net_pay is auto-calculated in the save() method of PayrollRecord
            payroll.save()
            count_updated += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count_updated} payroll records.'))
        if count_finalized > 0:
            self.stdout.write(self.style.SUCCESS(f'Finalized {count_finalized} records to Generated status.'))
