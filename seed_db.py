import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.students.models import StudentProfile
from apps.payroll.models import SalaryStructure, PayrollPolicy
import datetime

User = get_user_model()

# Create a Manager
manager, created = User.objects.get_or_create(username='manager', defaults={'role': 'Manager'})
if created:
    manager.set_password('password')
    manager.save()

# Create a Student User
student_user, created = User.objects.get_or_create(username='student1', defaults={'role': 'Student'})
if created:
    student_user.set_password('password')
    student_user.save()

# Create StudentProfile
sp, created = StudentProfile.objects.get_or_create(
    user=student_user,
    defaults={
        'student_id': 'STU001',
        'full_name': 'Test Student',
        'email': 'stu1@example.com',
        'phone': '12345678',
        'department': 'IT',
        'joining_date': datetime.date(2026, 1, 1),
        'designation': 'Intern',
        'status': 'Active'
    }
)
sp.status = 'Active' # Ensure it is active
sp.save()

# Create SalaryStructure
SalaryStructure.objects.get_or_create(
    student=sp,
    defaults={'base_stipend': 15000}
)

# Create Policy
PayrollPolicy.objects.get_or_create(name='Default Policy')

print("Seeded DB successfully")
