from django.contrib import admin
from .models import StudentProfile

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'department', 'designation', 'status')
    search_fields = ('student_id', 'full_name', 'email')
    list_filter = ('status', 'department', 'designation')
