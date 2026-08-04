from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    path('clients/', views.client_list, name='client_list'),
    path('assignments/', views.assignment_list, name='assignment_list'),
]
