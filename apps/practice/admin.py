from django.contrib import admin
from .models import Client, WorkType, Assignment, ClientVisit

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'status')
    search_fields = ('name', 'email')
    list_filter = ('status',)

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'work_type', 'deadline', 'status')
    list_filter = ('status', 'work_type')
    search_fields = ('title', 'client__name')
    filter_horizontal = ('assigned_students',)

@admin.register(ClientVisit)
class ClientVisitAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'client', 'assignment', 'work_type')
