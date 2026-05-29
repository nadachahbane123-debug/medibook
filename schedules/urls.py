from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    path('manage/', views.manage_availability, name='manage'),
    path('slots/<int:doctor_id>/', views.get_available_slots_json, name='slots_json'),
]
