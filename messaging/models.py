from django.db import models
from accounts.models import User
from appointments.models import Appointment


class Conversation(models.Model):
    """Conversation entre un patient et un médecin, liée optionnellement à un RDV"""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_conversations')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_conversations')
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conversation'
    )
    subject = models.CharField(max_length=200, default='Message')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversation'

    def __str__(self):
        return f"Conv {self.patient.get_full_name()} ↔ {self.doctor.get_full_name()}"

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'

    def __str__(self):
        return f"Msg de {self.sender.get_full_name()}: {self.content[:50]}"
