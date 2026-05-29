#!/bin/sh
echo "=== MediBook - Démarrage ==="

echo "Creating migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations patients
python manage.py makemigrations doctors
python manage.py makemigrations appointments
python manage.py makemigrations schedules
python manage.py makemigrations notifications
python manage.py makemigrations ai_orientation
python manage.py makemigrations dashboard
python manage.py makemigrations messaging

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating initial data (specialties)..."
python manage.py shell -c "
from doctors.models import Specialty
specialties = [
    ('Médecine Générale', '🏥', 'fièvre fatigue grippe bilan check-up ordonnance'),
    ('Cardiologie', '❤️', 'cœur palpitations douleur thoracique essoufflement hypertension'),
    ('Dermatologie', '🧴', 'peau boutons acné éruption démangeaisons eczéma'),
    ('Pédiatrie', '👶', 'enfant bébé nourrisson fièvre croissance vaccin'),
    ('Gynécologie', '🌸', 'règles grossesse contraception gynécologie kyste ovaire'),
    ('Ophtalmologie', '👁️', 'yeux vision myopie lunettes cataracte glaucome'),
    ('ORL', '👂', 'oreille nez gorge otite sinusite angine'),
    ('Dentisterie', '🦷', 'dent carie abcès gencive dentaire'),
    ('Neurologie', '🧠', 'tête migraine AVC épilepsie mémoire'),
    ('Orthopédie', '🦴', 'os fracture entorse dos lombalgie arthrose'),
    ('Gastroentérologie', '🫀', 'ventre estomac diarrhée constipation reflux'),
    ('Urologie', '💊', 'rein urine prostate infection urinaire'),
]
created = 0
for name, icon, keywords in specialties:
    _, c = Specialty.objects.get_or_create(name=name, defaults={'icon': icon, 'keywords': keywords})
    if c: created += 1
print(f'{created} spécialités créées.')
" 2>/dev/null || true

echo "Sending reminders (if any)..."
python manage.py send_reminders 2>/dev/null || true

echo "Starting server..."
exec gunicorn medibook_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120