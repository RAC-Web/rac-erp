from django.urls import path
from . import views

app_name = 'conveyance'

urlpatterns = [
    path('submit/', views.submit_conveyance, name='submit'),
    path('list/', views.conveyance_list, name='list'),
]
