from django.contrib import admin
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('signup/doctors/', views.doctor_form, name='doctor_signup'),
]
