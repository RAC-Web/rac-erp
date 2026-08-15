from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_add'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.AssignmentCreateView.as_view(), name='assignment_add'),
    path('assignments/<int:pk>/edit/', views.AssignmentUpdateView.as_view(), name='assignment_edit'),
    path('assignments/<int:pk>/status/', views.mark_assignment_status, name='assignment_status'),
]
