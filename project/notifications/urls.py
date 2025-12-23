from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('mark-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('ajax-mark-read/<int:notification_id>/', views.ajax_mark_as_read, name='ajax_mark_as_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
]
