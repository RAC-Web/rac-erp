from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_add'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('assignments/', views.assignment_list, name='assignment_list'),
]
