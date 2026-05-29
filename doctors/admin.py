from django.contrib import admin
from .models import Doctor, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'specialty', 'years_experience', 'is_active', 'rating']
    list_filter = ['specialty', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'license_number']
    raw_id_fields = ['user']
