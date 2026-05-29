from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError
from .models import Appointment, PatientProfile, Review, Consultation
from doctors.models import Doctor
from schedules.models import Availability, TimeSlot
from .forms import AppointmentForm, ReviewForm, CancellationForm, ConsultationForm
from notifications.utils import create_notification
import datetime


def get_or_create_patient_profile(user):
    profile, created = PatientProfile.objects.get_or_create(user=user)
    return profile


@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, pk=doctor_id, is_active=True)

    if not request.user.is_patient():
        messages.error(request, 'Seuls les patients peuvent réserver des rendez-vous.')
        return redirect('doctors:detail', pk=doctor_id)

    patient = get_or_create_patient_profile(request.user)

    # Récupérer les créneaux disponibles
    from ai_orientation.utils import classify_urgency
    available_slots = TimeSlot.objects.filter(
        availability__doctor=doctor,
        is_booked=False,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')[:30]

    if request.method == 'POST':
        form = AppointmentForm(request.POST, doctor=doctor)
        if form.is_valid():
            slot_id = request.POST.get('slot_id')
            slot = get_object_or_404(TimeSlot, pk=slot_id, is_booked=False)

            # Vérifier pas de conflit
            conflict = Appointment.objects.filter(
                doctor=doctor,
                date=slot.date,
                time=slot.start_time,
                status__in=['pending', 'confirmed']
            ).exists()

            if conflict:
                messages.error(request, 'Ce créneau vient d\'être réservé. Choisissez un autre.')
                return redirect('appointments:book', doctor_id=doctor_id)

            reason = form.cleaned_data['reason']
            urgency = classify_urgency(reason)

            try:
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    specialty=doctor.specialty,
                    date=slot.date,
                    time=slot.start_time,
                    end_time=slot.end_time,
                    reason=reason,
                    urgency=urgency,
                )
                slot.is_booked = True
                slot.appointment = appointment
                slot.save()

                # Notifications
                create_notification(
                    request.user,
                    f'Votre rendez-vous avec {doctor} est confirmé pour le {slot.date} à {slot.start_time}.',
                    'appointment_created'
                )
                create_notification(
                    doctor.user,
                    f'Nouveau rendez-vous avec {request.user.get_full_name()} le {slot.date} à {slot.start_time}.',
                    'new_patient'
                )

                # Email de confirmation
                send_appointment_confirmation_email(appointment)
                messages.success(request, 'Rendez-vous réservé avec succès ! Un email de confirmation vous a été envoyé.')
                return redirect('appointments:detail', pk=appointment.pk)
            except IntegrityError:
                messages.error(request, 'Erreur lors de la réservation. Veuillez réessayer.')
    else:
        form = AppointmentForm(doctor=doctor)

    context = {
        'doctor': doctor,
        'form': form,
        'available_slots': available_slots,
    }
    return render(request, 'appointments/book.html', context)


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Vérifier les droits
    user = request.user
    if user.is_patient() and appointment.patient.user != user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')
    if user.is_doctor() and appointment.doctor.user != user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')

    review_form = None
    consultation_form = None

    if appointment.status == 'completed':
        if user.is_patient() and not hasattr(appointment, 'review'):
            review_form = ReviewForm()
        if user.is_doctor() and not hasattr(appointment, 'consultation'):
            consultation_form = ConsultationForm()

    if request.method == 'POST':
        if 'submit_review' in request.POST and user.is_patient():
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                Review.objects.create(appointment=appointment, **review_form.cleaned_data)
                appointment.doctor.update_rating()
                messages.success(request, 'Avis publié !')
                return redirect('appointments:detail', pk=pk)

        elif 'submit_consultation' in request.POST and user.is_doctor():
            consultation_form = ConsultationForm(request.POST)
            if consultation_form.is_valid():
                Consultation.objects.create(appointment=appointment, **consultation_form.cleaned_data)
                messages.success(request, 'Compte-rendu enregistré.')
                return redirect('appointments:detail', pk=pk)

        elif 'update_status' in request.POST and user.is_doctor():
            new_status = request.POST.get('new_status')
            if new_status in ['confirmed', 'cancelled', 'completed', 'absent']:
                appointment.status = new_status
                appointment.save()
                create_notification(
                    appointment.patient.user,
                    f'Votre rendez-vous du {appointment.date} a été mis à jour : {appointment.get_status_display()}.',
                    'appointment_updated'
                )
                messages.success(request, 'Statut mis à jour.')
                return redirect('appointments:detail', pk=pk)

    context = {
        'appointment': appointment,
        'review_form': review_form,
        'consultation_form': consultation_form,
    }
    return render(request, 'appointments/detail.html', context)


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user

    if user.is_patient() and appointment.patient.user != user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')

    if not appointment.can_cancel():
        messages.error(request, 'Il n\'est plus possible d\'annuler ce rendez-vous (moins de 2h avant).')
        return redirect('appointments:detail', pk=pk)

    if request.method == 'POST':
        form = CancellationForm(request.POST)
        if form.is_valid():
            appointment.status = 'cancelled'
            appointment.cancelled_by = user
            appointment.cancellation_reason = form.cleaned_data['reason']
            appointment.save()

            # Libérer le créneau
            if hasattr(appointment, 'timeslot'):
                appointment.timeslot.is_booked = False
                appointment.timeslot.save()

            # Notification
            if user.is_patient():
                create_notification(
                    appointment.doctor.user,
                    f'Le rendez-vous du {appointment.date} avec {user.get_full_name()} a été annulé.',
                    'appointment_cancelled'
                )
            else:
                create_notification(
                    appointment.patient.user,
                    f'Votre rendez-vous du {appointment.date} avec {appointment.doctor} a été annulé.',
                    'appointment_cancelled'
                )

            messages.success(request, 'Rendez-vous annulé.')
            return redirect('dashboard:home')
    else:
        form = CancellationForm()

    return render(request, 'appointments/cancel.html', {'appointment': appointment, 'form': form})


@login_required
def appointment_list(request):
    user = request.user
    if user.is_patient():
        patient = get_or_create_patient_profile(user)
        appointments = Appointment.objects.filter(patient=patient).select_related('doctor__user', 'specialty')
    elif user.is_doctor():
        appointments = Appointment.objects.filter(doctor__user=user).select_related('patient__user', 'specialty')
    else:
        appointments = Appointment.objects.all().select_related('doctor__user', 'patient__user')

    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    context = {
        'appointments': appointments.order_by('-date', '-time'),
        'status_filter': status_filter,
    }
    return render(request, 'appointments/list.html', context)


@login_required
def reschedule_appointment(request, pk):
    """Modifier la date/heure d'un rendez-vous existant"""
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user

    # Droits
    if user.is_patient() and appointment.patient.user != user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')

    # Vérifier qu'on peut encore modifier
    if appointment.status not in ['pending', 'confirmed']:
        messages.error(request, 'Ce rendez-vous ne peut plus être modifié.')
        return redirect('appointments:detail', pk=pk)

    if not appointment.can_cancel():
        messages.error(request, 'Impossible de modifier ce rendez-vous moins de 2h avant l\'heure prévue.')
        return redirect('appointments:detail', pk=pk)

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        reason = request.POST.get('reason', appointment.reason).strip()

        if not slot_id:
            messages.error(request, 'Veuillez sélectionner un créneau.')
            return redirect('appointments:reschedule', pk=pk)

        slot = get_object_or_404(TimeSlot, pk=slot_id, is_booked=False)

        # Libérer l'ancien créneau
        try:
            old_slot = appointment.timeslot
            old_slot.is_booked = False
            old_slot.appointment = None
            old_slot.save()
        except Exception:
            pass

        # Mettre à jour le RDV
        old_date = appointment.date
        old_time = appointment.time
        appointment.date = slot.date
        appointment.time = slot.start_time
        appointment.end_time = slot.end_time
        appointment.reason = reason
        appointment.status = 'pending'
        appointment.save()

        # Réserver le nouveau créneau
        slot.is_booked = True
        slot.appointment = appointment
        slot.save()

        # Notifications
        create_notification(
            appointment.doctor.user,
            f'Le rendez-vous du {old_date} à {old_time} avec {user.get_full_name()} a été reporté au {slot.date} à {slot.start_time}.',
            'appointment_updated'
        )
        if user.is_doctor():
            create_notification(
                appointment.patient.user,
                f'Votre rendez-vous a été reporté au {slot.date} à {slot.start_time} par le médecin.',
                'appointment_updated'
            )

        messages.success(request, f'Rendez-vous reporté au {slot.date} à {slot.start_time}.')
        return redirect('appointments:detail', pk=appointment.pk)

    return render(request, 'appointments/reschedule.html', {'appointment': appointment})


def send_appointment_confirmation_email(appointment):
    """Envoie un email de confirmation au patient"""
    from django.core.mail import send_mail
    from django.conf import settings

    patient_email = appointment.patient.user.email
    if not patient_email:
        return

    subject = f'[MediBook] Confirmation de votre rendez-vous du {appointment.date}'
    message = f"""
Bonjour {appointment.patient.user.get_full_name()},

Votre rendez-vous a été enregistré avec succès sur MediBook.

📋 DÉTAILS DU RENDEZ-VOUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍⚕️ Médecin    : {appointment.doctor}
🏥 Spécialité : {appointment.specialty.name if appointment.specialty else 'Non précisé'}
📅 Date       : {appointment.date.strftime('%A %d %B %Y')}
⏰ Heure      : {appointment.time.strftime('%H:%M')}
📍 Cabinet    : {appointment.doctor.cabinet_address}
📝 Motif      : {appointment.reason}

⚡ Statut : En attente de confirmation

Référence : RDV-{appointment.pk:06d}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vous pouvez gérer votre rendez-vous sur : http://localhost:8001/appointments/{appointment.pk}/

⚠️ En cas d'empêchement, pensez à annuler au moins 2h avant.

Cordialement,
L'équipe MediBook
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@medibook.ma'),
            recipient_list=[patient_email],
            fail_silently=True,
        )
    except Exception:
        pass


@login_required
def patient_medical_history(request, patient_id):
    """Historique médical d'un patient — visible par le médecin lors d'une consultation"""
    user = request.user

    if not (user.is_doctor() or user.is_admin_user()):
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard:home')

    patient_profile = get_object_or_404(PatientProfile, pk=patient_id)

    # Vérifier que le médecin a déjà eu un RDV avec ce patient
    if user.is_doctor():
        has_relation = Appointment.objects.filter(
            doctor__user=user,
            patient=patient_profile
        ).exists()
        if not has_relation:
            messages.error(request, 'Vous n\'avez pas de relation médicale avec ce patient.')
            return redirect('dashboard:home')

    # Historique complet
    all_appointments = Appointment.objects.filter(
        patient=patient_profile
    ).select_related('doctor__user', 'specialty').prefetch_related('consultation', 'review').order_by('-date')

    context = {
        'patient': patient_profile,
        'all_appointments': all_appointments,
        'total': all_appointments.count(),
        'completed': all_appointments.filter(status='completed').count(),
    }
    return render(request, 'appointments/patient_history.html', context)
