from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('mark/', views.mark_attendance, name='mark'),
    path('list/', views.attendance_list, name='list'),
    path('add/', views.AttendanceCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.AttendanceUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.AttendanceDeleteView.as_view(), name='delete'),
]
