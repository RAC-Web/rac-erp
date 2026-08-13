import datetime
import calendar
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.students.models import StudentProfile
from apps.payroll.utils import generate_daily_payroll_log, recalculate_monthly_payroll


class Command(BaseCommand):
    help = 'Automatically generates daily payroll logs and updates monthly payroll records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to process (YYYY-MM-DD). Defaults to today.',
        )
        parser.add_argument(
            '--backfill',
            action='store_true',
            help='Backfill all days from the 1st of the month up to the target date.',
        )
        parser.add_argument(
            '--student-id',
            type=int,
            help='Process only a specific student by ID.',
        )

    def handle(self, *args, **kwargs):
        # Determine target date
        date_str = kwargs.get('date')
        backfill = kwargs.get('backfill', False)
        student_id = kwargs.get('student_id')

        if date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f'Invalid date format: {date_str}. Use YYYY-MM-DD.'))
                return
        else:
            target_date = timezone.now().date()

        first_day_of_month = datetime.date(target_date.year, target_date.month, 1)

        # Get students to process
        if student_id:
            students = StudentProfile.objects.filter(id=student_id, status='Active')
            if not students.exists():
                self.stderr.write(self.style.ERROR(f'No active student found with ID: {student_id}'))
                return
        else:
            students = StudentProfile.objects.filter(status='Active')

        self.stdout.write(self.style.NOTICE(
            f'Processing payroll for {students.count()} active student(s)...'
        ))

        # Determine which dates to process
        if backfill:
            dates_to_process = []
            current = first_day_of_month
            while current <= target_date:
                dates_to_process.append(current)
                current += datetime.timedelta(days=1)
            self.stdout.write(self.style.NOTICE(
                f'Backfilling from {first_day_of_month} to {target_date} ({len(dates_to_process)} days)'
            ))
        else:
            dates_to_process = [target_date]

        count_logs_created = 0
        count_logs_updated = 0
        count_payrolls_updated = 0
        count_finalized = 0

        for student in students:
            # Only process if they have a salary structure
            if not hasattr(student, 'salary_structure'):
                self.stdout.write(self.style.WARNING(
                    f'  [SKIP] {student.full_name} -- no salary structure defined.'
                ))
                continue

            # Generate daily logs for each date
            for process_date in dates_to_process:
                from apps.payroll.models import DailyPayrollLog
                existing = DailyPayrollLog.objects.filter(
                    student=student, date=process_date
                ).exists()

                log = generate_daily_payroll_log(student, process_date)

                if existing:
                    count_logs_updated += 1
                else:
                    count_logs_created += 1

            # Recalculate monthly payroll
            payroll = recalculate_monthly_payroll(student, first_day_of_month)
            if payroll:
                count_payrolls_updated += 1
                if payroll.status == 'Generated':
                    count_finalized += 1

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Daily Payroll Generation Complete!'))
        self.stdout.write(self.style.SUCCESS(f'  Date(s): {dates_to_process[0]} to {dates_to_process[-1]}'))
        self.stdout.write(self.style.SUCCESS(f'  Daily logs created: {count_logs_created}'))
        self.stdout.write(self.style.SUCCESS(f'  Daily logs updated: {count_logs_updated}'))
        self.stdout.write(self.style.SUCCESS(f'  Monthly payrolls updated: {count_payrolls_updated}'))
        if count_finalized > 0:
            self.stdout.write(self.style.SUCCESS(
                f'  Records finalized to Generated: {count_finalized}'
            ))
        self.stdout.write(self.style.SUCCESS('=' * 50))
