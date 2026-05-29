"""
Commande Django : send_reminders
Envoie des notifications de rappel 24h avant chaque rendez-vous.

Usage : python manage.py send_reminders
Planification cron (dans entrypoint ou crontab) :
  0 8 * * * python manage.py send_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.models import Appointment
from notifications.utils import create_notification
import datetime


class Command(BaseCommand):
    help = 'Envoie des rappels de rendez-vous 24h à l\'avance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Heures avant le RDV pour envoyer le rappel (défaut: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule sans envoyer de notifications'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']

        now = timezone.now()
        target_start = now + datetime.timedelta(hours=hours - 1)
        target_end = now + datetime.timedelta(hours=hours + 1)

        # Trouver les RDV dans la fenêtre cible
        appointments = Appointment.objects.filter(
            status__in=['confirmed', 'pending'],
        ).select_related('patient__user', 'doctor__user', 'specialty')

        reminders_sent = 0

        for apt in appointments:
            # Construire le datetime du RDV
            apt_datetime = timezone.make_aware(
                datetime.datetime.combine(apt.date, apt.time)
            )

            # Vérifier si dans la fenêtre de rappel
            if target_start <= apt_datetime <= target_end:
                message = (
                    f"⏰ Rappel : Vous avez un rendez-vous demain avec {apt.doctor} "
                    f"à {apt.time.strftime('%H:%M')} "
                    f"({'spécialité : ' + apt.specialty.name if apt.specialty else ''})."
                )

                if not dry_run:
                    # Notifier le patient
                    create_notification(
                        apt.patient.user,
                        message,
                        notification_type='reminder'
                    )
                    # Notifier le médecin
                    create_notification(
                        apt.doctor.user,
                        f"⏰ Rappel : RDV demain avec {apt.patient.user.get_full_name()} à {apt.time.strftime('%H:%M')}.",
                        notification_type='reminder'
                    )
                    reminders_sent += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Rappel envoyé : RDV #{apt.pk} — {apt.patient.user.get_full_name()} ↔ {apt.doctor}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [DRY-RUN] Rappel simulé : RDV #{apt.pk} — {apt.patient.user.get_full_name()} ↔ {apt.doctor}')
                    )
                    reminders_sent += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY-RUN] {reminders_sent} rappels simulés (aucun envoyé).'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ {reminders_sent} rappels envoyés avec succès.'))

        # Stats
        total_upcoming = Appointment.objects.filter(
            status__in=['confirmed', 'pending'],
            date__gte=now.date()
        ).count()
        self.stdout.write(f'📊 Total RDV à venir : {total_upcoming}')
