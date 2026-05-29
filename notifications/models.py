from django.db import models
from accounts.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('appointment_created', 'Rendez-vous créé'),
        ('appointment_updated', 'Rendez-vous mis à jour'),
        ('appointment_cancelled', 'Rendez-vous annulé'),
        ('new_patient', 'Nouveau patient'),
        ('reminder', 'Rappel'),
        ('info', 'Information'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'

    def __str__(self):
        return f"Notif pour {self.user}: {self.message[:50]}"
