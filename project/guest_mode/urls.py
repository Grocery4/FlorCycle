from django.urls import path

from . import views

app_name = 'guest_mode'

urlpatterns = [
    path('', views.show_form, name='show_form'),
]
