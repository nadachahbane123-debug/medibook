from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from doctors.models import Doctor, Specialty
from appointments.models import Appointment, PatientProfile
from accounts.models import User


def global_search(request):
    """Recherche globale dans médecins, spécialités et RDV"""
    query = request.GET.get('q', '').strip()
    results = {
        'doctors': [],
        'specialties': [],
        'appointments': [],
        'query': query,
        'total': 0,
    }

    if query and len(query) >= 2:
        # Médecins
        doctors = Doctor.objects.filter(
            is_active=True
        ).filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialty__name__icontains=query) |
            Q(bio__icontains=query) |
            Q(cabinet_address__icontains=query)
        ).select_related('user', 'specialty').distinct()[:8]
        results['doctors'] = doctors

        # Spécialités
        specialties = Specialty.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(keywords__icontains=query)
        )[:6]
        results['specialties'] = specialties

        # RDV (seulement si connecté)
        if request.user.is_authenticated:
            user = request.user
            if user.is_patient():
                patient, _ = PatientProfile.objects.get_or_create(user=user)
                appointments = Appointment.objects.filter(
                    patient=patient
                ).filter(
                    Q(reason__icontains=query) |
                    Q(doctor__user__first_name__icontains=query) |
                    Q(doctor__user__last_name__icontains=query) |
                    Q(specialty__name__icontains=query)
                ).select_related('doctor__user', 'specialty').order_by('-date')[:5]
            elif user.is_doctor():
                appointments = Appointment.objects.filter(
                    doctor__user=user
                ).filter(
                    Q(reason__icontains=query) |
                    Q(patient__user__first_name__icontains=query) |
                    Q(patient__user__last_name__icontains=query)
                ).select_related('patient__user', 'specialty').order_by('-date')[:5]
            else:
                appointments = Appointment.objects.filter(
                    Q(reason__icontains=query) |
                    Q(doctor__user__last_name__icontains=query) |
                    Q(patient__user__last_name__icontains=query)
                ).select_related('doctor__user', 'patient__user').order_by('-date')[:5]
            results['appointments'] = appointments

        results['total'] = len(results['doctors']) + len(results['specialties']) + len(results['appointments'])

    return render(request, 'search/results.html', results)
