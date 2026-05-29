from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from appointments.models import PatientProfile


@login_required
def update_medical_info(request):
    """Met à jour les informations médicales du patient"""
    if not request.user.is_patient():
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')

    patient, _ = PatientProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        patient.blood_type = request.POST.get('blood_type', '')
        patient.allergies = request.POST.get('allergies', '')
        patient.chronic_conditions = request.POST.get('chronic_conditions', '')
        patient.emergency_contact = request.POST.get('emergency_contact', '')
        patient.emergency_phone = request.POST.get('emergency_phone', '')
        patient.insurance_number = request.POST.get('insurance_number', '')
        patient.save()
        messages.success(request, 'Informations médicales mises à jour.')

    return redirect('accounts:profile')
