"""
Export PDF des rendez-vous - MediBook
Utilise WeasyPrint ou fallback HTML imprimable
"""
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from appointments.models import Appointment, PatientProfile


@login_required
def export_appointment_pdf(request, pk):
    """Exporte un rendez-vous en PDF"""
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user

    # Vérification des droits
    if user.is_patient() and appointment.patient.user != user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès non autorisé.")
    if user.is_doctor() and appointment.doctor.user != user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès non autorisé.")

    context = {
        'appointment': appointment,
        'generated_at': timezone.now(),
        'site_name': 'MediBook',
    }

    try:
        import weasyprint
        html_string = render_to_string('pdf/appointment_pdf.html', context)
        html = weasyprint.HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="RDV-{appointment.pk}-MediBook.pdf"'
        return response
    except ImportError:
        # Fallback : HTML imprimable si WeasyPrint pas installé
        html_string = render_to_string('pdf/appointment_pdf.html', context)
        response = HttpResponse(html_string, content_type='text/html')
        return response


@login_required
def export_patient_history_pdf(request):
    """Exporte l'historique complet du patient"""
    user = request.user
    if not user.is_patient():
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    patient, _ = PatientProfile.objects.get_or_create(user=user)
    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related('doctor__user', 'specialty').order_by('-date')

    context = {
        'patient': patient,
        'appointments': appointments,
        'generated_at': timezone.now(),
        'site_name': 'MediBook',
    }

    try:
        import weasyprint
        html_string = render_to_string('pdf/history_pdf.html', context)
        html = weasyprint.HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Historique-{user.username}-MediBook.pdf"'
        return response
    except ImportError:
        html_string = render_to_string('pdf/history_pdf.html', context)
        return HttpResponse(html_string, content_type='text/html')


@login_required
def export_prescription_pdf(request, consultation_id):
    """Génère l'ordonnance PDF d'une consultation"""
    from appointments.models import Consultation
    from django.utils import timezone

    consultation = get_object_or_404(Consultation, pk=consultation_id)

    # Vérification droits
    user = request.user
    if user.is_doctor() and consultation.appointment.doctor.user != user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    if user.is_patient() and consultation.appointment.patient.user != user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    context = {
        'consultation': consultation,
        'generated_at': timezone.now(),
    }

    try:
        import weasyprint
        html_string = render_to_string('pdf/prescription_pdf.html', context)
        html = weasyprint.HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Ordonnance-{consultation.pk}-MediBook.pdf"'
        return response
    except ImportError:
        html_string = render_to_string('pdf/prescription_pdf.html', context)
        return HttpResponse(html_string, content_type='text/html')
