from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Conversation, Message
from accounts.models import User
from doctors.models import Doctor
from appointments.models import Appointment
from notifications.utils import create_notification


@login_required
def inbox(request):
    """Liste de toutes les conversations de l'utilisateur"""
    user = request.user
    if user.is_patient():
        conversations = Conversation.objects.filter(patient=user).select_related('doctor', 'appointment')
    elif user.is_doctor():
        conversations = Conversation.objects.filter(doctor=user).select_related('patient', 'appointment')
    else:
        conversations = Conversation.objects.all().select_related('patient', 'doctor')

    # Ajouter le compteur de non-lus pour chaque conversation
    conv_data = []
    for conv in conversations:
        unread = conv.unread_count(user)
        last_msg = conv.get_last_message()
        conv_data.append({
            'conv': conv,
            'unread': unread,
            'last_msg': last_msg,
        })

    return render(request, 'messaging/inbox.html', {
        'conv_data': conv_data,
        'total_unread': sum(c['unread'] for c in conv_data),
    })


@login_required
def conversation_detail(request, pk):
    """Affiche et envoie des messages dans une conversation"""
    user = request.user
    conv = get_object_or_404(Conversation, pk=pk)

    # Vérifier les droits
    if user != conv.patient and user != conv.doctor and not user.is_admin_user():
        messages.error(request, 'Accès non autorisé.')
        return redirect('messaging:inbox')

    # Marquer les messages comme lus
    conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=conv,
                sender=user,
                content=content,
            )
            # Notification à l'autre personne
            recipient = conv.doctor if user == conv.patient else conv.patient
            create_notification(
                recipient,
                f'Nouveau message de {user.get_full_name()}: {content[:60]}...' if len(content) > 60 else f'Nouveau message de {user.get_full_name()}: {content}',
                'info',
                link=f'/messaging/{conv.pk}/'
            )
            # Si requête AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': msg.pk,
                    'content': msg.content,
                    'sender': user.get_full_name(),
                    'time': msg.created_at.strftime('%H:%M'),
                    'is_mine': True,
                })
            return redirect('messaging:detail', pk=pk)

    all_messages = conv.messages.select_related('sender').order_by('created_at')
    other_user = conv.doctor if user == conv.patient else conv.patient

    return render(request, 'messaging/conversation.html', {
        'conversation': conv,
        'all_messages': all_messages,
        'other_user': other_user,
    })


@login_required
def start_conversation(request, doctor_id):
    """Démarrer une conversation avec un médecin"""
    user = request.user
    doctor_user = get_object_or_404(User, pk=doctor_id, role='doctor')

    if not user.is_patient():
        messages.error(request, 'Seuls les patients peuvent initier une conversation.')
        return redirect('doctors:list')

    # Chercher une conversation existante
    conv = Conversation.objects.filter(patient=user, doctor=doctor_user).first()

    if not conv:
        subject = request.POST.get('subject', 'Nouvelle conversation')
        conv = Conversation.objects.create(
            patient=user,
            doctor=doctor_user,
            subject=subject,
        )

    return redirect('messaging:detail', pk=conv.pk)


@login_required
def start_from_appointment(request, appointment_id):
    """Démarrer une conversation depuis un RDV"""
    user = request.user
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    # Vérifier les droits
    if user.is_patient() and appointment.patient.user != user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')

    patient_user = appointment.patient.user
    doctor_user = appointment.doctor.user

    # Chercher ou créer la conversation liée au RDV
    conv, created = Conversation.objects.get_or_create(
        patient=patient_user,
        doctor=doctor_user,
        appointment=appointment,
        defaults={'subject': f'RDV du {appointment.date} — {appointment.reason[:50]}'}
    )

    return redirect('messaging:detail', pk=conv.pk)


@login_required
def unread_messages_count(request):
    """API JSON pour le badge de messages non lus"""
    user = request.user
    if user.is_patient():
        count = Message.objects.filter(
            conversation__patient=user,
            is_read=False
        ).exclude(sender=user).count()
    else:
        count = Message.objects.filter(
            conversation__doctor=user,
            is_read=False
        ).exclude(sender=user).count()
    return JsonResponse({'count': count})
