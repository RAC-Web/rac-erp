from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('announcement/send/', views.send_announcement, name='send_announcement'),
    path('notifications/dismiss-popup/', views.dismiss_popup, name='dismiss_popup'),
]
