from django.contrib import admin
from .models import Availability, TimeSlot, Unavailability

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'get_day_of_week_display', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['availability', 'date', 'start_time', 'is_booked']
    list_filter = ['is_booked', 'date']

@admin.register(Unavailability)
class UnavailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'start_date', 'end_date', 'reason']
