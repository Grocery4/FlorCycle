from django.contrib import admin
from django.urls import path, re_path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('redirect/', views.redirect_handler, name='redirect_handler'),
    path('setup/', views.setup, name='setup_page'),
    path('settings/', views.settings, name='settings_page'),
    path('setup/partners', views.partner_setup, name='partner_setup_page'),
    path('partner-mode/', views.homepage_readonly, name='homepage_readonly'),
    re_path(r'^(?:home/)?$', views.homepage, name='homepage'),
    path('log-period/', views.add_period, name='add_period'),
    path('logs/', views.cycle_logs, name='logs_page'),
    path('add-log/', views.add_log, name='add_log'),
    path('stats/', views.stats, name='stats'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('ajax/load-log/', views.ajax_load_log, name='ajax_load_log'),
    path('ajax/navigate-calendar/', views.ajax_navigate_calendar, name='ajax_navigate_calendar'),
    path('ajax/load-stats', views.ajax_load_stats, name='ajax_load_stats'),
    path('ajax/get-top-symptoms/', views.ajax_get_top_symptoms, name='ajax_get_top_symptoms'),
    path('ajax/get-available-items/', views.ajax_get_available_items, name='ajax_get_available_items'),
    path('ajax/analyze-item/', views.ajax_analyze_item, name='ajax_analyze_item'),
    path('ajax/search-logs/', views.ajax_search_logs, name='ajax_search_logs'),
    path('backup/', views.backup_data, name='backup_data'),
    path('restore/', views.restore_data, name='restore_data'),
    path('reset-data/', views.reset_data, name='reset_data'),
]
