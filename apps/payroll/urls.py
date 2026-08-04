from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('list/', views.payroll_list, name='list'),
    path('payslip/<int:pk>/', views.generate_payslip_pdf, name='payslip_pdf'),
]
