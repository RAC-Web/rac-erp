from django.contrib import admin
from .models import SalaryStructure, PayrollRecord

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('student', 'base_stipend')
    search_fields = ('student__full_name',)

@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'base_stipend', 'net_pay', 'status')
    list_filter = ('status', 'month')
    search_fields = ('student__full_name',)
