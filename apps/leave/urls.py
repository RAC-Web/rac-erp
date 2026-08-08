from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    path('apply/', views.apply_leave, name='apply_leave'),
    path('list/', views.leave_list, name='leave_list'),
    path('<int:pk>/approve/', views.approve_leave, name='approve'),
    path('<int:pk>/reject/', views.reject_leave, name='reject'),
    path('add/', views.LeaveCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.LeaveUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.LeaveDeleteView.as_view(), name='delete'),
    path('<int:pk>/pdf/', views.download_leave_pdf, name='pdf'),
]
