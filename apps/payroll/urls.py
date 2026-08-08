from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('list/', views.payroll_list, name='list'),
    path('api/calculate/', views.calculate_deductions_api, name='api_calculate'),
    path('generate/', views.PayrollCreateView.as_view(), name='generate'),
    path('edit/<int:pk>/', views.PayrollUpdateView.as_view(), name='edit'),
    path('payslip/<int:pk>/', views.generate_payslip_pdf, name='payslip_pdf'),
]
