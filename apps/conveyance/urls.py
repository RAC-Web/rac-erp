from django.urls import path
from . import views

app_name = 'conveyance'

urlpatterns = [
    path('submit/', views.submit_conveyance, name='submit'),
    path('list/', views.conveyance_list, name='list'),
    path('<int:pk>/approve/', views.approve_conveyance, name='approve'),
    path('<int:pk>/reject/', views.reject_conveyance, name='reject'),
    path('add/', views.ConveyanceCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.ConveyanceUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ConveyanceDeleteView.as_view(), name='delete'),
]
