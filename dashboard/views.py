from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from appointments.models import Appointment, PatientProfile
from doctors.models import Doctor, Specialty
from accounts.models import User
from notifications.models import Notification
import datetime


@login_required
def dashboard_home(request):
    user = request.user
    if user.is_patient():
        return patient_dashboard(request)
    elif user.is_doctor():
        return doctor_dashboard(request)
    else:
        return admin_dashboard(request)


def patient_dashboard(request):
    user = request.user
    patient, _ = PatientProfile.objects.get_or_create(user=user)
    today = timezone.now().date()

    upcoming = Appointment.objects.filter(
        patient=patient,
        date__gte=today,
        status__in=['pending', 'confirmed']
    ).select_related('doctor__user', 'specialty').order_by('date', 'time')[:5]

    past = Appointment.objects.filter(
        patient=patient,
        date__lt=today
    ).select_related('doctor__user', 'specialty').order_by('-date')[:5]

    cancelled = Appointment.objects.filter(
        patient=patient,
        status='cancelled'
    ).select_related('doctor__user').order_by('-updated_at')[:3]

    notifications = Notification.objects.filter(user=user, is_read=False)[:5]

    stats = {
        'total': Appointment.objects.filter(patient=patient).count(),
        'upcoming': upcoming.count(),
        'completed': Appointment.objects.filter(patient=patient, status='completed').count(),
        'cancelled': Appointment.objects.filter(patient=patient, status='cancelled').count(),
    }

    context = {
        'upcoming_appointments': upcoming,
        'past_appointments': past,
        'cancelled_appointments': cancelled,
        'notifications': notifications,
        'stats': stats,
        'patient': patient,
    }
    return render(request, 'dashboard/patient.html', context)


def doctor_dashboard(request):
    user = request.user
    try:
        doctor = Doctor.objects.get(user=user)
    except Doctor.DoesNotExist:
        return render(request, 'dashboard/doctor_setup.html')

    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    today_appointments = Appointment.objects.filter(
        doctor=doctor, date=today
    ).select_related('patient__user').order_by('time')

    week_appointments = Appointment.objects.filter(
        doctor=doctor, date__range=[week_start, week_end]
    ).select_related('patient__user', 'specialty').order_by('date', 'time')

    stats = {
        'total': Appointment.objects.filter(doctor=doctor).count(),
        'today': today_appointments.count(),
        'week': week_appointments.count(),
        'confirmed': Appointment.objects.filter(doctor=doctor, status='confirmed').count(),
        'pending': Appointment.objects.filter(doctor=doctor, status='pending').count(),
        'completed': Appointment.objects.filter(doctor=doctor, status='completed').count(),
        'cancelled': Appointment.objects.filter(doctor=doctor, status='cancelled').count(),
    }

    monthly_stats = []
    for i in range(6):
        month_date = today.replace(day=1) - datetime.timedelta(days=i * 28)
        count = Appointment.objects.filter(
            doctor=doctor,
            date__year=month_date.year,
            date__month=month_date.month,
        ).count()
        monthly_stats.insert(0, {
            'month': month_date.strftime('%b %Y'),
            'count': count
        })

    notifications = Notification.objects.filter(user=user, is_read=False)[:5]

    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'week_appointments': week_appointments,
        'stats': stats,
        'monthly_stats': monthly_stats,
        'notifications': notifications,
    }
    return render(request, 'dashboard/doctor.html', context)


def admin_dashboard(request):
    today = timezone.now().date()

    stats = {
        'total_patients': PatientProfile.objects.count(),
        'total_doctors': Doctor.objects.filter(is_active=True).count(),
        'total_appointments': Appointment.objects.count(),
        'today_appointments': Appointment.objects.filter(date=today).count(),
        'pending': Appointment.objects.filter(status='pending').count(),
        'confirmed': Appointment.objects.filter(status='confirmed').count(),
        'cancelled': Appointment.objects.filter(status='cancelled').count(),
        'completed': Appointment.objects.filter(status='completed').count(),
    }

    top_specialties = Specialty.objects.annotate(
        rdv_count=Count('appointment'),
        confirmed_count=Count('appointment', filter=Q(appointment__status='confirmed')),
        completed_count=Count('appointment', filter=Q(appointment__status='completed')),
        cancelled_count=Count('appointment', filter=Q(appointment__status='cancelled')),
    ).order_by('-rdv_count')[:8]

    top_doctors = Doctor.objects.annotate(
        rdv_count=Count('appointments')
    ).filter(is_active=True).order_by('-rdv_count')[:5]

    weekly_data = []
    for i in range(7):
        day = today - datetime.timedelta(days=6 - i)
        count = Appointment.objects.filter(date=day).count()
        weekly_data.append({'day': day.strftime('%a'), 'count': count})

    context = {
        'stats': stats,
        'top_specialties': top_specialties,
        'top_doctors': top_doctors,
        'weekly_data': weekly_data,
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def doctor_calendar(request):
    if not request.user.is_doctor():
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    doctor = get_object_or_404(Doctor, user=request.user)
    offset = int(request.GET.get('offset', 0))
    today = timezone.now().date() + datetime.timedelta(days=offset)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    week_appointments = Appointment.objects.filter(
        doctor=doctor,
        date__range=[week_start, week_end]
    ).select_related('patient__user').order_by('date', 'time')

    week_days = []
    real_today = timezone.now().date()
    for i in range(7):
        day = week_start + datetime.timedelta(days=i)
        day_apts = [a for a in week_appointments if a.date == day]
        week_days.append({
            'date': day,
            'appointments': day_apts,
            'count': len(day_apts),
            'is_today': day == real_today,
        })

    context = {
        'doctor': doctor,
        'week_days': week_days,
        'week_start': week_start,
        'week_end': week_end,
        'hours': list(range(8, 20)),
        'offset': offset,
    }
    return render(request, 'dashboard/calendar.html', context)


@login_required
def ai_stats(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')

    from ai_orientation.utils import suggest_specialty
    from collections import Counter

    recent_appointments = Appointment.objects.order_by('-created_at')[:100]
    specialty_counts = Counter()
    urgency_counts = Counter()

    for apt in recent_appointments:
        if apt.reason:
            result = suggest_specialty(apt.reason)
            specialty_counts[result['specialty']] += 1
            urgency_counts[apt.urgency] += 1

    context = {
        'top_specialties': specialty_counts.most_common(8),
        'urgency_distribution': dict(urgency_counts),
        'total_analyzed': len(recent_appointments),
    }
    return render(request, 'dashboard/ai_stats.html', context)


@login_required
def manage_doctors(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        action = request.POST.get('action')
        try:
            doc = Doctor.objects.get(pk=doctor_id)
            if action == 'activate':
                doc.is_active = True
                doc.save()
                messages.success(request, f'{doc} activé.')
            elif action == 'deactivate':
                doc.is_active = False
                doc.save()
                messages.success(request, f'{doc} désactivé.')
        except Doctor.DoesNotExist:
            messages.error(request, 'Médecin introuvable.')
        return redirect('dashboard:manage_doctors')

    doctors = Doctor.objects.all().select_related('user', 'specialty').order_by('is_active', 'user__last_name')
    specialties = Specialty.objects.all()
    return render(request, 'dashboard/manage_doctors.html', {'doctors': doctors, 'specialties': specialties})


@login_required
def advanced_stats(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')

    import json

    today = timezone.now().date()

    monthly = []
    for i in range(11, -1, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        month_date = today.replace(year=y, month=m, day=1)
        count = Appointment.objects.filter(
            date__year=month_date.year,
            date__month=month_date.month
        ).count()
        cancelled = Appointment.objects.filter(
            date__year=month_date.year,
            date__month=month_date.month,
            status='cancelled'
        ).count()
        monthly.append({
            'month': month_date.strftime('%b %Y'),
            'total': count,
            'cancelled': cancelled,
            'taux': round(cancelled / count * 100, 1) if count > 0 else 0
        })

    hourly = []
    for h in range(7, 20):
        count = Appointment.objects.filter(time__hour=h).count()
        hourly.append({'hour': f'{h:02d}h', 'count': count})

    total = Appointment.objects.count()
    completed = Appointment.objects.filter(status='completed').count()
    cancelled_total = Appointment.objects.filter(status='cancelled').count()
    top_rated = Doctor.objects.filter(total_reviews__gt=0).order_by('-rating')[:5]

    context = {
        'monthly': monthly,
        'monthly_json': json.dumps(monthly),
        'hourly': hourly,
        'hourly_json': json.dumps(hourly),
        'stats': {
            'total': total,
            'completed': completed,
            'cancelled': cancelled_total,
            'taux_annulation': round(cancelled_total / total * 100, 1) if total > 0 else 0,
            'taux_completion': round(completed / total * 100, 1) if total > 0 else 0,
        },
        'top_rated': top_rated,
    }
    return render(request, 'stats/advanced.html', context)


@login_required
def manage_users(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')

    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    total = users.count()
    paginator = Paginator(users, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'dashboard/manage_users.html', {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'total': total,
    })


@login_required
def toggle_user(request, pk):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')
    if request.method == 'POST':
        try:
            u = User.objects.get(pk=pk)
            if u != request.user:
                u.is_active = not u.is_active
                u.save()
                status = 'activé' if u.is_active else 'désactivé'
                messages.success(request, f'{u.get_full_name()} {status}.')
        except User.DoesNotExist:
            messages.error(request, 'Utilisateur introuvable.')
    return redirect('dashboard:manage_users')


@login_required
def manage_specialties(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            icon = request.POST.get('icon', '🏥').strip()
            keywords = request.POST.get('keywords', '').strip()
            description = request.POST.get('description', '').strip()
            if name:
                Specialty.objects.get_or_create(
                    name=name,
                    defaults={'icon': icon, 'keywords': keywords, 'description': description}
                )
                messages.success(request, f'Spécialité "{name}" ajoutée.')
            return redirect('dashboard:manage_specialties')

        elif action == 'edit':
            spec_id = request.POST.get('spec_id')
            try:
                spec = Specialty.objects.get(pk=spec_id)
                spec.name = request.POST.get('name', spec.name).strip()
                spec.icon = request.POST.get('icon', spec.icon).strip()
                spec.keywords = request.POST.get('keywords', spec.keywords).strip()
                spec.description = request.POST.get('description', spec.description).strip()
                spec.save()
                messages.success(request, f'Spécialité "{spec.name}" mise à jour.')
            except Specialty.DoesNotExist:
                messages.error(request, 'Spécialité introuvable.')
            return redirect('dashboard:manage_specialties')

    specialties = Specialty.objects.annotate(
        rdv_count=Count('appointment'),
        doctor_count=Count('doctors')
    ).order_by('name')

    return render(request, 'dashboard/manage_specialties.html', {
        'specialties': specialties,
    })


@login_required
def delete_specialty(request, pk):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')
    if request.method == 'POST':
        try:
            spec = Specialty.objects.get(pk=pk)
            name = spec.name
            spec.delete()
            messages.success(request, f'Spécialité "{name}" supprimée.')
        except Specialty.DoesNotExist:
            messages.error(request, 'Spécialité introuvable.')
    return redirect('dashboard:manage_specialties')


@login_required
def save_user(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        role = request.POST.get('role', 'patient')
        password = request.POST.get('password', '').strip()

        if user_id:
            try:
                u = User.objects.get(pk=user_id)
                u.first_name = first_name
                u.last_name = last_name
                u.email = email
                u.username = username
                u.role = role
                if password:
                    u.set_password(password)
                u.save()
                messages.success(request, f'{u.get_full_name()} mis à jour.')
            except User.DoesNotExist:
                messages.error(request, 'Utilisateur introuvable.')
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Le username "{username}" est déjà pris.')
            else:
                u = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                u.role = role
                u.save()
                messages.success(request, f'{u.get_full_name()} créé avec succès.')
    return redirect('dashboard:manage_users')


@login_required
def delete_user(request, pk):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')
    if request.method == 'POST':
        try:
            u = User.objects.get(pk=pk)
            if u != request.user:
                name = u.get_full_name()
                u.delete()
                messages.success(request, f'{name} supprimé.')
            else:
                messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte.')
        except User.DoesNotExist:
            messages.error(request, 'Utilisateur introuvable.')
    return redirect('dashboard:manage_users')


@login_required
def save_doctor(request):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        specialty_id = request.POST.get('specialty')
        years_experience = request.POST.get('years_experience', '').strip()
        consultation_fee = request.POST.get('consultation_fee', '').strip()
        cabinet_address = request.POST.get('cabinet_address', '').strip()
        license_number = request.POST.get('license_number', '').strip()
        password = request.POST.get('password', '').strip()

        if doctor_id:
            try:
                doc = Doctor.objects.get(pk=doctor_id)
                doc.user.first_name = first_name
                doc.user.last_name = last_name
                doc.user.email = email
                if password:
                    doc.user.set_password(password)
                doc.user.save()
                if specialty_id:
                    doc.specialty = Specialty.objects.get(pk=specialty_id)
                if years_experience:
                    doc.years_experience = years_experience
                if consultation_fee:
                    doc.consultation_fee = consultation_fee
                doc.cabinet_address = cabinet_address
                doc.license_number = license_number
                doc.save()
                messages.success(request, f'{doc} mis à jour.')
            except Doctor.DoesNotExist:
                messages.error(request, 'Médecin introuvable.')
        else:
            if not password:
                messages.error(request, 'Le mot de passe est obligatoire.')
                return redirect('dashboard:manage_doctors')
            if User.objects.filter(email=email).exists():
                messages.error(request, f'Email "{email}" déjà utilisé.')
                return redirect('dashboard:manage_doctors')
            username = f"dr.{last_name.lower().replace(' ', '')}"
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"dr.{last_name.lower().replace(' ', '')}{counter}"
                counter += 1
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            user.role = 'doctor'
            user.save()
            doc = Doctor.objects.create(user=user)
            if specialty_id:
                doc.specialty = Specialty.objects.get(pk=specialty_id)
            if years_experience:
                doc.years_experience = years_experience
            if consultation_fee:
                doc.consultation_fee = consultation_fee
            doc.cabinet_address = cabinet_address
            doc.license_number = license_number
            doc.save()
            messages.success(request, f'Dr. {first_name} {last_name} créé avec succès.')
    return redirect('dashboard:manage_doctors')


@login_required
def delete_doctor(request, pk):
    if not request.user.is_admin_user():
        return redirect('dashboard:home')
    if request.method == 'POST':
        try:
            doc = Doctor.objects.get(pk=pk)
            name = str(doc)
            doc.user.delete()
            messages.success(request, f'{name} supprimé.')
        except Doctor.DoesNotExist:
            messages.error(request, 'Médecin introuvable.')
    return redirect('dashboard:manage_doctors')