from django.db import models
from apps.students.models import StudentProfile
from apps.practice.models import Client, Assignment

class Conveyance(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='conveyances')
    date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    submitted_on = models.DateTimeField(auto_now_add=True)
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Conveyance Claim - {self.student.full_name} ({self.date})"

class ConveyanceItem(models.Model):
    conveyance = models.ForeignKey(Conveyance, on_delete=models.CASCADE, related_name='items')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True, blank=True)
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)
    transport = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='conveyance_bills/', blank=True, null=True)

    def __str__(self):
        return f"{self.from_location} to {self.to_location} ({self.amount})"
