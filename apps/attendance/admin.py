from django.contrib import admin
from .models import AttendancePolicy, Attendance, AttendanceLog

@admin.register(AttendancePolicy)
class AttendancePolicyAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'grace_time', 'late_time', 'absent_time')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time_in', 'time_out', 'status', 'location')
    list_filter = ('status', 'date', 'location')
    search_fields = ('student__full_name', 'student__student_id')

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'manager', 'old_status', 'new_status', 'changed_at')
    list_filter = ('changed_at',)
    search_fields = ('manager__username', 'attendance__student__full_name')
