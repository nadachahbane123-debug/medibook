from django.db import models
from doctors.models import Doctor
import datetime


class Availability(models.Model):
    DAY_CHOICES = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'),
        (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=30, help_text='Durée en minutes')
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Disponibilité'
        verbose_name_plural = 'Disponibilités'
        unique_together = ['doctor', 'day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def generate_slots_for_date(self, date):
        """Génère les créneaux pour une date donnée"""
        slots = []
        current = datetime.datetime.combine(date, self.start_time)
        end = datetime.datetime.combine(date, self.end_time)
        delta = datetime.timedelta(minutes=self.slot_duration)

        while current + delta <= end:
            slot, created = TimeSlot.objects.get_or_create(
                availability=self,
                date=date,
                start_time=current.time(),
                defaults={'end_time': (current + delta).time()}
            )
            slots.append(slot)
            current += delta
        return slots


class TimeSlot(models.Model):
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='timeslot'
    )

    class Meta:
        unique_together = ['availability', 'date', 'start_time']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time} - {'Réservé' if self.is_booked else 'Libre'}"


class Unavailability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='unavailabilities')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Indisponibilité'

    def __str__(self):
        return f"{self.doctor} indisponible du {self.start_date} au {self.end_date}"

class LeaveDay(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leave_days')
    date = models.DateField(verbose_name='Jour de congé')
    reason = models.CharField(max_length=200, blank=True, verbose_name='Motif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Jour de congé'
        verbose_name_plural = 'Jours de congé'
        unique_together = ['doctor', 'date']
        ordering = ['date']

    def __str__(self):
        return f"{self.doctor} — congé le {self.date}"
    
