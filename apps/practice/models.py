from django.db import models
from apps.students.models import StudentProfile

class Client(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return self.name

class WorkType(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, help_text="e.g., Audit, Tax, VAT, Accounting")

    def __str__(self):
        return f"{self.category} - {self.name}"
    
    class Meta:
        ordering = ['category', 'name']

class Assignment(models.Model):
    STATUS_CHOICES = (
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    work_type = models.ForeignKey(WorkType, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not Started')
    assigned_students = models.ManyToManyField(StudentProfile, related_name='assignments', blank=True)

    def __str__(self):
        return f"{self.title} ({self.client.name})"
