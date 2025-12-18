from django.contrib import admin
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/doctors/', views.doctor_form, name='doctor_signup'),
    path('signup/partner/', views.partner_form, name='partner_signup'),
    path('signup/', views.standard_form, name='standard_signup'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
]
