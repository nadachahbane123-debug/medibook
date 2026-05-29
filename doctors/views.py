from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Doctor, Specialty
from appointments.models import Appointment, Review


def doctor_list(request):
    doctors = Doctor.objects.filter(is_active=True).select_related('user', 'specialty')
    specialties = Specialty.objects.all()

    specialty_id = request.GET.get('specialty')
    search = request.GET.get('search', '')
    min_rating = request.GET.get('min_rating', '')
    max_fee = request.GET.get('max_fee', '')
    min_exp = request.GET.get('min_exp', '')
    sort = request.GET.get('sort', 'name')

    if specialty_id and specialty_id != 'None':
        doctors = doctors.filter(specialty_id=specialty_id)
    if search:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(specialty__name__icontains=search) |
            Q(bio__icontains=search)
        )
    if min_rating:
        try:
            doctors = doctors.filter(rating__gte=float(min_rating))
        except ValueError:
            pass
    if max_fee:
        try:
            doctors = doctors.filter(consultation_fee__lte=float(max_fee))
        except ValueError:
            pass
    if min_exp:
        try:
            doctors = doctors.filter(years_experience__gte=int(min_exp))
        except ValueError:
            pass

    sort_map = {
        'name': 'user__last_name',
        'rating': '-rating',
        'experience': '-years_experience',
        'fee': 'consultation_fee',
    }
    doctors = doctors.order_by(sort_map.get(sort, 'user__last_name'))

    paginator = Paginator(doctors, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'doctors': page_obj,
        'specialties': specialties,
        'selected_specialty': specialty_id,
        'search': search,
        'min_rating': min_rating,
        'max_fee': max_fee,
        'min_exp': min_exp,
        'sort': sort,
        'total_count': paginator.count,
    }
    return render(request, 'doctors/doctor_list.html', context)


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk, is_active=True)
    reviews = Review.objects.filter(
        appointment__doctor=doctor
    ).select_related('appointment__patient__user').order_by('-created_at')[:10]

    from schedules.models import Availability
    availabilities = Availability.objects.filter(doctor=doctor, is_available=True)

    context = {
        'doctor': doctor,
        'reviews': reviews,
        'availabilities': availabilities,
    }
    return render(request, 'doctors/doctor_detail.html', context)


@login_required
def doctor_profile_edit(request):
    if not request.user.is_doctor():
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')
    return redirect('accounts:profile')


@login_required
def save_doctor_profile(request):
    if not request.user.is_doctor():
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard:home')

    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        doctor.license_number = request.POST.get('license_number', doctor.license_number)
        doctor.phone_professional = request.POST.get('phone_professional', doctor.phone_professional)
        doctor.years_experience = request.POST.get('years_experience', doctor.years_experience)
        doctor.consultation_fee = request.POST.get('consultation_fee', doctor.consultation_fee)
        doctor.cabinet_address = request.POST.get('cabinet_address', doctor.cabinet_address)
        doctor.bio = request.POST.get('bio', doctor.bio)
        doctor.is_active = 'is_active' in request.POST

        specialty_id = request.POST.get('specialty')
        if specialty_id:
            try:
                doctor.specialty = Specialty.objects.get(pk=specialty_id)
            except Specialty.DoesNotExist:
                pass

        if 'photo' in request.FILES:
            doctor.photo = request.FILES['photo']

        doctor.save()
        messages.success(request, 'Profil professionnel mis à jour avec succès.')

    return redirect('accounts:profile')