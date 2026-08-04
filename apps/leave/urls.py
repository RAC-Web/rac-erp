from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    path('apply/', views.apply_leave, name='apply_leave'),
    path('list/', views.leave_list, name='leave_list'),
]
