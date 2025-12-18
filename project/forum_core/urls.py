from django.urls import path
from . import views

app_name = 'forum_core'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.home, name='home'),
    path('create/', views.create_thread, name='create_thread'),
    path('thread/<int:thread_id>/', views.thread, name='thread'),
    path('doctors/', views.doctor_ranking, name='doctor_ranking'),
]