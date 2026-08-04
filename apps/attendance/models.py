from django.db import models
from django.conf import settings
from apps.students.models import StudentProfile

class AttendancePolicy(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_time = models.TimeField()
    late_time = models.TimeField()
    half_day_time = models.TimeField()
    absent_time = models.TimeField()
    working_hour = models.DecimalField(max_digits=5, decimal_places=2, help_text="Standard working hours per day")
    late_to_absent_ratio = models.IntegerField(default=3, help_text="Number of late days to convert to 1 absent")
    late_to_halfday_ratio = models.IntegerField(default=2, help_text="Number of late days to convert to 1 half-day")

    def __str__(self):
        return f"Policy: {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    class Meta:
        verbose_name_plural = "Attendance Policies"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Late', 'Late'),
        ('Absent', 'Absent'),
        ('Half Day', 'Half Day'),
        ('Holiday', 'Holiday'),
        ('Leave', 'Leave'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    
    # Track location if client visit is marked
    location = models.CharField(max_length=50, default='Office')

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.status})"

class AttendanceLog(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='logs')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    reason = models.TextField()
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log: {self.attendance.date} by {self.manager.username if self.manager else 'System'}"
