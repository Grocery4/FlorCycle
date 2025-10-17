from django.contrib import admin
from django.urls import path, re_path

from . import views

app_name = 'dashboard'

urlpatterns = [
    re_path(r'^(?:home/)?$', views.home, name='homepage')
]
