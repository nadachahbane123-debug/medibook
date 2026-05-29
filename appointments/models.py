from django.db import models
from django.utils import timezone
from accounts.models import User
from doctors.models import Doctor, Specialty


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Profil Patient'

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
        ('completed', 'Terminé'),
        ('absent', 'Absent'),
    ]
    URGENCY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Modérée'),
        ('high', 'Élevée'),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='low')
    notes = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_appointments'
    )
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['-date', '-time']
        unique_together = ['doctor', 'date', 'time']

    def __str__(self):
        return f"RDV {self.patient} avec {self.doctor} le {self.date} à {self.time}"

    def is_past(self):
        from datetime import datetime
        rdv_dt = datetime.combine(self.date, self.time)
        return timezone.make_aware(rdv_dt) < timezone.now()

    def can_cancel(self):
        """Patient peut annuler jusqu'à 2h avant"""
        from datetime import datetime, timedelta
        rdv_dt = datetime.combine(self.date, self.time)
        rdv_aware = timezone.make_aware(rdv_dt)
        return rdv_aware > timezone.now() + timezone.timedelta(hours=2)


class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avis'

    def __str__(self):
        return f"Avis {self.rating}★ pour {self.appointment.doctor}"


class Consultation(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation')
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation: {self.appointment}"
