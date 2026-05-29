from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Availability, TimeSlot, Unavailability, LeaveDay
from doctors.models import Doctor
import datetime


@login_required
def manage_availability(request):
    if not request.user.is_doctor():
        messages.error(request, 'Accès réservé aux médecins.')
        return redirect('dashboard:home')

    doctor = get_object_or_404(Doctor, user=request.user)
    availabilities = Availability.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    unavailabilities = Unavailability.objects.filter(doctor=doctor, end_date__gte=timezone.now().date())
    leave_days = LeaveDay.objects.filter(doctor=doctor, date__gte=timezone.now().date()).order_by('date')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_availability':
            from .forms import AvailabilityForm
            form = AvailabilityForm(request.POST)
            if form.is_valid():
                avail = form.save(commit=False)
                avail.doctor = doctor
                avail.save()
                generate_slots_bulk(avail)
                messages.success(request, 'Disponibilité ajoutée.')
                return redirect('schedules:manage')

        elif action == 'delete_availability':
            avail_id = request.POST.get('avail_id')
            Availability.objects.filter(pk=avail_id, doctor=doctor).delete()
            messages.success(request, 'Disponibilité supprimée.')
            return redirect('schedules:manage')

        elif action == 'add_unavailability':
            from .forms import UnavailabilityForm
            form = UnavailabilityForm(request.POST)
            if form.is_valid():
                unav = form.save(commit=False)
                unav.doctor = doctor
                unav.save()
                TimeSlot.objects.filter(
                    availability__doctor=doctor,
                    date__range=[unav.start_date, unav.end_date],
                    is_booked=False
                ).delete()
                messages.success(request, 'Période d\'indisponibilité enregistrée.')
                return redirect('schedules:manage')

        elif action == 'delete_unavailability':
            unav_id = request.POST.get('unav_id')
            Unavailability.objects.filter(pk=unav_id, doctor=doctor).delete()
            messages.success(request, 'Période supprimée.')
            return redirect('schedules:manage')

        elif action == 'add_leave':
            leave_date = request.POST.get('leave_date')
            leave_reason = request.POST.get('leave_reason', '')
            if leave_date:
                try:
                    LeaveDay.objects.get_or_create(
                        doctor=doctor,
                        date=leave_date,
                        defaults={'reason': leave_reason}
                    )
                    # Supprimer les créneaux de ce jour
                    TimeSlot.objects.filter(
                        availability__doctor=doctor,
                        date=leave_date,
                        is_booked=False
                    ).delete()
                    messages.success(request, f'Jour de congé ajouté pour le {leave_date}.')
                except Exception:
                    messages.error(request, 'Ce jour de congé existe déjà.')
                return redirect('schedules:manage')

        elif action == 'delete_leave':
            leave_id = request.POST.get('leave_id')
            LeaveDay.objects.filter(pk=leave_id, doctor=doctor).delete()
            messages.success(request, 'Jour de congé supprimé.')
            return redirect('schedules:manage')

    from .forms import AvailabilityForm, UnavailabilityForm
    context = {
        'availabilities': availabilities,
        'unavailabilities': unavailabilities,
        'leave_days': leave_days,
        'avail_form': AvailabilityForm(),
        'unav_form': UnavailabilityForm(),
        'doctor': doctor,
    }
    return render(request, 'schedules/manage.html', context)


def generate_slots_bulk(availability, days=30):
    today = timezone.now().date()
    for i in range(days):
        date = today + datetime.timedelta(days=i)
        if date.weekday() == availability.day_of_week:
            # Ne pas générer si jour de congé
            if not LeaveDay.objects.filter(
                doctor=availability.doctor,
                date=date
            ).exists():
                availability.generate_slots_for_date(date)


def get_available_slots_json(request, doctor_id):
    from django.http import JsonResponse
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    date_str = request.GET.get('date')
    try:
        date = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return JsonResponse({'slots': []})

    # Vérifier si jour de congé
    if LeaveDay.objects.filter(doctor=doctor, date=date).exists():
        return JsonResponse({'slots': [], 'message': 'Jour de congé'})

    slots = TimeSlot.objects.filter(
        availability__doctor=doctor,
        date=date,
        is_booked=False
    ).order_by('start_time')

    data = [{'id': s.pk, 'start': str(s.start_time)[:5], 'end': str(s.end_time)[:5]} for s in slots]
    return JsonResponse({'slots': data})