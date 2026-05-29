from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('calendar/', views.doctor_calendar, name='calendar'),
    path('ai-stats/', views.ai_stats, name='ai_stats'),
    path('doctors/', views.manage_doctors, name='manage_doctors'),
    path('stats/', views.advanced_stats, name='advanced_stats'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:pk>/toggle/', views.toggle_user, name='toggle_user'),
    path('specialties/', views.manage_specialties, name='manage_specialties'),
    path('specialties/<int:pk>/delete/', views.delete_specialty, name='delete_specialty'),
    path('users/save/', views.save_user, name='save_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('doctors/save/', views.save_doctor, name='save_doctor'),
    path('doctors/<int:pk>/delete/', views.delete_doctor, name='delete_doctor'),
]