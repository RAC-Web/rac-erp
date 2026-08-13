from django.contrib import admin
from .models import SalaryStructure, PayrollRecord, PayrollPolicy, DailyPayrollLog

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('student', 'base_stipend')
    search_fields = ('student__full_name',)

@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'base_stipend', 'net_pay', 'status')
    list_filter = ('status', 'month')
    search_fields = ('student__full_name',)

@admin.register(PayrollPolicy)
class PayrollPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'deduct_unapproved_leave', 'sandwich_rule_active', 'late_deduction_active')

@admin.register(DailyPayrollLog)
class DailyPayrollLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'attendance_status', 'is_working_day', 'per_day_salary', 
                    'daily_conveyance', 'late_deduction', 'leave_deduction', 'sandwich_deduction', 'daily_net')
    list_filter = ('attendance_status', 'is_working_day', 'date')
    search_fields = ('student__full_name',)
    date_hierarchy = 'date'
    ordering = ['-date', 'student__full_name']

