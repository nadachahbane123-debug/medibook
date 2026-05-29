from django.contrib import admin
from .models import Appointment, PatientProfile, Review, Consultation

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'blood_type', 'created_at']
    search_fields = ['user__first_name', 'user__last_name']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'time', 'status', 'urgency']
    list_filter = ['status', 'urgency', 'date']
    search_fields = ['patient__user__first_name', 'doctor__user__last_name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'rating', 'created_at']

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'created_at']
