from django.db import models
from django.conf import settings

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=100)
    joining_date = models.DateField()
    designation = models.CharField(max_length=100)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Alumni', 'Alumni'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    documents = models.FileField(upload_to='documents/', blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"
