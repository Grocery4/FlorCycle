from django.contrib import admin
from django.urls import path, re_path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('setup/', views.setup, name='setup_page'),
    path('settings/', views.settings, name='settings_page'),
    re_path(r'^(?:home/)?$', views.homepage, name='homepage'),
    path('logs/', views.cycle_logs, name='logs_page'),
]
