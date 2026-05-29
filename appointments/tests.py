"""
Tests unitaires MediBook
Couvre : modèles, vues, formulaires, IA
Lancer : python manage.py test
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from doctors.models import Doctor, Specialty
from appointments.models import Appointment, PatientProfile, Review
from schedules.models import Availability, TimeSlot
from notifications.models import Notification
from notifications.utils import create_notification
from ai_orientation.utils import suggest_specialty, classify_urgency
import datetime


# ============================================================
# HELPERS
# ============================================================
def create_patient(username='patient_test', password='TestPass123!'):
    user = User.objects.create_user(
        username=username, password=password,
        first_name='Ahmed', last_name='Benali',
        email=f'{username}@test.com', role='patient'
    )
    PatientProfile.objects.get_or_create(user=user)
    return user


def create_doctor(username='doctor_test', password='TestPass123!'):
    specialty, _ = Specialty.objects.get_or_create(
        name='Cardiologie',
        defaults={'icon': '❤️', 'keywords': 'cœur palpitations douleur thoracique'}
    )
    user = User.objects.create_user(
        username=username, password=password,
        first_name='Dr. Sara', last_name='Khalil',
        email=f'{username}@test.com', role='doctor'
    )
    doctor = Doctor.objects.create(
        user=user, specialty=specialty,
        license_number=f'LIC-{username}',
        phone_professional='0600000000',
        cabinet_address='Rabat, Maroc',
        years_experience=10, is_active=True
    )
    return user, doctor


# ============================================================
# TEST MODELS
# ============================================================
class UserModelTest(TestCase):

    def test_create_patient_user(self):
        user = create_patient()
        self.assertEqual(user.role, 'patient')
        self.assertTrue(user.is_patient())
        self.assertFalse(user.is_doctor())

    def test_create_doctor_user(self):
        user, doctor = create_doctor()
        self.assertEqual(user.role, 'doctor')
        self.assertTrue(user.is_doctor())
        self.assertFalse(user.is_patient())

    def test_full_name_or_username(self):
        user = create_patient()
        self.assertEqual(user.get_full_name_or_username(), 'Ahmed Benali')

    def test_user_str(self):
        user = create_patient()
        self.assertIn('Ahmed Benali', str(user))


class SpecialtyModelTest(TestCase):

    def test_create_specialty(self):
        s = Specialty.objects.create(
            name='Dermatologie',
            icon='🧴',
            keywords='peau, boutons, acné, eczéma'
        )
        self.assertEqual(str(s), 'Dermatologie')
        self.assertIn('peau', s.get_keywords_list())

    def test_keywords_list(self):
        s = Specialty.objects.create(name='ORL', keywords='oreille, nez, gorge')
        keywords = s.get_keywords_list()
        self.assertEqual(len(keywords), 3)
        self.assertIn('oreille', keywords)


class DoctorModelTest(TestCase):

    def test_doctor_str(self):
        _, doctor = create_doctor()
        self.assertIn('Dr. Sara', str(doctor))

    def test_doctor_is_active_by_default(self):
        _, doctor = create_doctor()
        self.assertTrue(doctor.is_active)

    def test_doctor_update_rating(self):
        patient_user = create_patient()
        _, doctor = create_doctor()
        patient = PatientProfile.objects.get(user=patient_user)
        specialty = doctor.specialty

        apt = Appointment.objects.create(
            patient=patient, doctor=doctor, specialty=specialty,
            date=timezone.now().date(),
            time=datetime.time(9, 0),
            reason='Test', status='completed'
        )
        Review.objects.create(appointment=apt, rating=4)
        doctor.update_rating()
        doctor.refresh_from_db()
        self.assertEqual(float(doctor.rating), 4.0)
        self.assertEqual(doctor.total_reviews, 1)


class AppointmentModelTest(TestCase):

    def setUp(self):
        self.patient_user = create_patient()
        _, self.doctor = create_doctor()
        self.patient = PatientProfile.objects.get(user=self.patient_user)

    def test_create_appointment(self):
        apt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            specialty=self.doctor.specialty,
            date=timezone.now().date() + datetime.timedelta(days=3),
            time=datetime.time(10, 0),
            reason='Douleur thoracique',
            status='pending'
        )
        self.assertEqual(apt.status, 'pending')
        self.assertEqual(apt.urgency, 'low')
        self.assertIn('patient=', str(apt) or 'RDV')

    def test_can_cancel_future_appointment(self):
        future_date = timezone.now().date() + datetime.timedelta(days=7)
        apt = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            specialty=self.doctor.specialty,
            date=future_date, time=datetime.time(14, 0),
            reason='Test', status='confirmed'
        )
        self.assertTrue(apt.can_cancel())

    def test_is_past_for_old_appointment(self):
        past_date = timezone.now().date() - datetime.timedelta(days=5)
        apt = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            specialty=self.doctor.specialty,
            date=past_date, time=datetime.time(9, 0),
            reason='Test', status='completed'
        )
        self.assertTrue(apt.is_past())

    def test_appointment_unique_constraint(self):
        from django.db import IntegrityError
        date = timezone.now().date() + datetime.timedelta(days=2)
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            specialty=self.doctor.specialty,
            date=date, time=datetime.time(11, 0), reason='Premier'
        )
        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                patient=self.patient, doctor=self.doctor,
                specialty=self.doctor.specialty,
                date=date, time=datetime.time(11, 0), reason='Doublon'
            )


# ============================================================
# TEST NOTIFICATIONS
# ============================================================
class NotificationTest(TestCase):

    def test_create_notification(self):
        user = create_patient()
        create_notification(user, 'Test notification', 'info')
        notifs = Notification.objects.filter(user=user)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().message, 'Test notification')
        self.assertFalse(notifs.first().is_read)

    def test_notification_mark_read(self):
        user = create_patient()
        notif = Notification.objects.create(user=user, message='Test', is_read=False)
        notif.is_read = True
        notif.save()
        self.assertTrue(Notification.objects.get(pk=notif.pk).is_read)


# ============================================================
# TEST AI ORIENTATION
# ============================================================
class AIOrientationTest(TestCase):

    def test_cardiology_suggestion(self):
        result = suggest_specialty('douleur thoracique palpitations essoufflement cœur')
        self.assertEqual(result['specialty'], 'Cardiologie')
        self.assertGreater(result['confidence'], 0)

    def test_dermatology_suggestion(self):
        result = suggest_specialty('boutons peau rougeurs acné démangeaisons eczéma')
        self.assertEqual(result['specialty'], 'Dermatologie')

    def test_pediatrics_suggestion(self):
        result = suggest_specialty('enfant bébé fièvre nourrisson croissance vaccin')
        self.assertEqual(result['specialty'], 'Pédiatrie')

    def test_dentistry_suggestion(self):
        result = suggest_specialty('douleur dent carie abcès dentaire gencive')
        self.assertEqual(result['specialty'], 'Dentisterie')

    def test_general_medicine_fallback(self):
        result = suggest_specialty('xyz abc 123 inconnu')
        self.assertIn('specialty', result)
        self.assertIn('confidence', result)

    def test_empty_symptoms(self):
        result = suggest_specialty('')
        self.assertEqual(result['specialty'], 'Médecine Générale')

    def test_urgency_high(self):
        self.assertEqual(classify_urgency('douleur intense sang urgence'), 'high')

    def test_urgency_medium(self):
        self.assertEqual(classify_urgency('fièvre élevée depuis plusieurs jours'), 'medium')

    def test_urgency_low(self):
        self.assertEqual(classify_urgency('rendez-vous de routine check-up'), 'low')

    def test_result_has_required_keys(self):
        result = suggest_specialty('migraine maux de tête')
        required_keys = ['specialty', 'confidence', 'alternatives', 'message']
        for key in required_keys:
            self.assertIn(key, result)


# ============================================================
# TEST VUES (Views)
# ============================================================
class HomeViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_doctor_list_loads(self):
        response = self.client.get(reverse('doctors:list'))
        self.assertEqual(response.status_code, 200)

    def test_ai_suggest_loads(self):
        response = self.client.get(reverse('ai_orientation:suggest'))
        self.assertEqual(response.status_code, 200)


class AuthViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_patient(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newpatient',
            'first_name': 'Fatima',
            'last_name': 'Zahra',
            'email': 'fatima@test.com',
            'phone': '0600000001',
            'password1': 'Django2026!Test',
            'password2': 'Django2026!Test',
        })
        self.assertTrue(User.objects.filter(username='newpatient').exists())
        new_user = User.objects.get(username='newpatient')
        self.assertEqual(new_user.role, 'patient')

    def test_login_valid_credentials(self):
        user = create_patient('logintest')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'logintest',
            'password': 'TestPass123!'
        })
        self.assertRedirects(response, reverse('dashboard:home'))

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'nobody',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        user = create_patient('logouttest')
        self.client.login(username='logouttest', password='TestPass123!')
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, '/')


class DashboardViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.patient_user = create_patient('dash_patient')
        _, self.doctor = create_doctor('dash_doctor')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)

    def test_patient_dashboard(self):
        self.client.login(username='dash_patient', password='TestPass123!')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)

    def test_doctor_dashboard(self):
        self.client.login(username='dash_doctor', password='TestPass123!')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)


class AppointmentViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.patient_user = create_patient('apt_patient')
        self.doctor_user, self.doctor = create_doctor('apt_doctor')

    def test_appointment_list_requires_login(self):
        response = self.client.get(reverse('appointments:list'))
        self.assertEqual(response.status_code, 302)

    def test_appointment_list_logged_in(self):
        self.client.login(username='apt_patient', password='TestPass123!')
        response = self.client.get(reverse('appointments:list'))
        self.assertEqual(response.status_code, 200)

    def test_book_appointment_page_loads(self):
        self.client.login(username='apt_patient', password='TestPass123!')
        response = self.client.get(reverse('appointments:book', kwargs={'doctor_id': self.doctor.pk}))
        self.assertEqual(response.status_code, 200)

    def test_doctor_cannot_book_appointment(self):
        self.client.login(username='apt_doctor', password='TestPass123!')
        response = self.client.get(reverse('appointments:book', kwargs={'doctor_id': self.doctor.pk}))
        self.assertNotEqual(response.status_code, 200)

    def test_notifications_count_api(self):
        self.client.login(username='apt_patient', password='TestPass123!')
        response = self.client.get(reverse('notifications:count'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('count', response.json())


class AIApiTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_ai_api_post(self):
        import json
        # Create specialties for the test
        Specialty.objects.get_or_create(name='Cardiologie', defaults={'icon': '❤️', 'keywords': 'cœur palpitations'})
        response = self.client.post(
            reverse('ai_orientation:api'),
            data=json.dumps({'symptoms': 'douleur thoracique palpitations'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('specialty', data)
        self.assertIn('confidence', data)
        self.assertIn('urgency', data)

    def test_ai_api_empty_symptoms(self):
        import json
        response = self.client.post(
            reverse('ai_orientation:api'),
            data=json.dumps({'symptoms': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_ai_api_get_not_allowed(self):
        response = self.client.get(reverse('ai_orientation:api'))
        self.assertEqual(response.status_code, 405)
