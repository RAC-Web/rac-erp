from django.test import TestCase, Client
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.attendance.models import AttendancePolicy, Attendance
from apps.leave.models import LeaveType, LeaveRequest
from apps.payroll.models import SalaryStructure, PayrollRecord
from django.utils import timezone
from decimal import Decimal
import datetime


def create_student(username, full_name, student_id, email):
    """Helper to create a test student user and profile."""
    user = User.objects.create_user(username=username, password='pass1234', role='Student')
    profile = StudentProfile.objects.create(
        user=user,
        full_name=full_name,
        student_id=student_id,
        email=email,
        phone='01700000000',
        department='Audit',
        joining_date=datetime.date.today(),
        designation='Trainee',
    )
    return user, profile


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', password='pass1234', role='Student')
        self.assertEqual(user.role, 'Student')
        self.assertTrue(user.check_password('pass1234'))

    def test_create_principal(self):
        user = User.objects.create_user(username='principal1', password='pass1234', role='Principal')
        self.assertEqual(user.role, 'Principal')


class StudentProfileTest(TestCase):
    def setUp(self):
        self.user, self.profile = create_student('student1', 'Test Student', 'STU001', 'student1@test.com')

    def test_profile_creation(self):
        self.assertEqual(str(self.profile), 'Test Student (STU001)')

    def test_profile_linked_to_user(self):
        self.assertEqual(self.profile.user, self.user)


class AttendanceModelTest(TestCase):
    def setUp(self):
        self.user, self.profile = create_student('att_student', 'Att Student', 'STU002', 'att@test.com')

    def test_mark_attendance(self):
        att = Attendance.objects.create(
            student=self.profile,
            date=datetime.date.today(),
            time_in=datetime.time(9, 0),
            status='Present'
        )
        self.assertEqual(att.status, 'Present')
        self.assertEqual(str(att), f'Att Student - {datetime.date.today()} (Present)')

    def test_unique_attendance_per_day(self):
        Attendance.objects.create(
            student=self.profile, date=datetime.date.today(),
            time_in=datetime.time(9, 0), status='Present'
        )
        with self.assertRaises(Exception):
            Attendance.objects.create(
                student=self.profile, date=datetime.date.today(),
                time_in=datetime.time(10, 0), status='Late'
            )


class LeaveModelTest(TestCase):
    def setUp(self):
        self.user, self.profile = create_student('leave_student', 'Leave Student', 'STU003', 'leave@test.com')
        self.leave_type = LeaveType.objects.create(name='Casual Leave')

    def test_leave_request_total_days(self):
        req = LeaveRequest.objects.create(
            student=self.profile, leave_type=self.leave_type,
            start_date=datetime.date(2026, 8, 1), end_date=datetime.date(2026, 8, 3),
            reason='Personal work'
        )
        self.assertEqual(req.total_days, 3)
        self.assertEqual(req.status, 'Pending')


class PayrollModelTest(TestCase):
    def setUp(self):
        self.user, self.profile = create_student('pay_student', 'Pay Student', 'STU004', 'pay@test.com')

    def test_net_pay_calculation(self):
        record = PayrollRecord.objects.create(
            student=self.profile,
            month=datetime.date(2026, 8, 1),
            base_stipend=Decimal('10000'),
            conveyance_allowance=Decimal('2000'),
            bonus=Decimal('500'),
            late_deduction=Decimal('300'),
            leave_deduction=Decimal('200'),
            other_deduction=Decimal('0')
        )
        expected = Decimal('12000')  # 10000+2000+500 - 300-200-0
        self.assertEqual(record.net_pay, expected)


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewuser', password='pass1234', role='Principal')

    def test_dashboard_requires_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_when_logged_in(self):
        self.client.login(username='viewuser', password='pass1234')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_renders(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
