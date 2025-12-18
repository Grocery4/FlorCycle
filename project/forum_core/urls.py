from django.urls import path
from . import views

app_name = 'forum_core'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.home, name='home'),
    path('create/', views.create_thread, name='create_thread'),
    path('thread/<int:thread_id>/', views.thread, name='thread'),
    path('thread/<int:thread_id>/edit/', views.edit_thread, name='edit_thread'),
    path('thread/<int:thread_id>/delete/', views.delete_thread, name='delete_thread'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('doctors/', views.doctor_ranking, name='doctor_ranking'),
]