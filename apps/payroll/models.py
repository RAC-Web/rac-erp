from django.db import models
from apps.students.models import StudentProfile

class SalaryStructure(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='salary_structure')
    base_stipend = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monthly Base Stipend")
    
    def __str__(self):
        return f"Structure for {self.student.full_name}"

class PayrollRecord(models.Model):
    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('Generated', 'Generated'),
        ('Paid', 'Paid')
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='payrolls')
    month = models.DateField(help_text="Use the 1st of the month, e.g., 2026-08-01 for Aug 2026")
    base_stipend = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additions
    conveyance_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions
    late_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leave_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Net Pay
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    generated_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.net_pay = (self.base_stipend + self.conveyance_allowance + self.bonus) - (self.late_deduction + self.leave_deduction + self.other_deduction)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payroll - {self.student.full_name} ({self.month.strftime('%b %Y')})"
    
    class Meta:
        unique_together = ('student', 'month')

class PayrollPolicy(models.Model):
    name = models.CharField(max_length=100, default='Default Policy')
    deduct_unapproved_leave = models.BooleanField(default=True, help_text="Deduct 1 day salary for unapproved absences")
    sandwich_rule_active = models.BooleanField(default=True, help_text="Deduct holiday salary if absent adjacent to holiday")
    late_deduction_active = models.BooleanField(default=True)
    first_lates_for_penalty = models.IntegerField(default=3, help_text="Number of initial late days that equal 1 absent day")
    subsequent_lates_for_penalty = models.IntegerField(default=2, help_text="Number of subsequent late days that equal 1 absent day")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Payroll Policies"


class DailyPayrollLog(models.Model):
    """Tracks daily payroll breakdown for each student - auto-generated every day."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='daily_payroll_logs')
    date = models.DateField()
    
    # Daily amounts
    per_day_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                         help_text="Base stipend / 30")
    daily_conveyance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Daily status tracking
    attendance_status = models.CharField(max_length=20, default='N/A',
                                          help_text="Present/Late/Absent/Leave/Holiday/Weekend")
    is_working_day = models.BooleanField(default=True)
    
    # Deductions for this day
    late_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leave_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sandwich_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Net for this day
    daily_net = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-calculate daily net
        earnings = self.per_day_salary + self.daily_conveyance
        deductions = self.late_deduction + self.leave_deduction + self.sandwich_deduction
        self.daily_net = earnings - deductions
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.attendance_status}) Net: {self.daily_net}"
    
    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']
        verbose_name = "Daily Payroll Log"
        verbose_name_plural = "Daily Payroll Logs"
