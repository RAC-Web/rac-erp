from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('attendance/', views.attendance_report, name='attendance'),
    path('attendance/excel/', views.attendance_report_excel, name='attendance_excel'),
    path('payroll/', views.payroll_report, name='payroll'),
    path('payroll/excel/', views.payroll_report_excel, name='payroll_excel'),
]
