from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .utils import suggest_specialty, classify_urgency
from doctors.models import Specialty, Doctor
from appointments.models import Appointment
from django.db.models import Count
from django.utils import timezone
import datetime


def ai_suggest(request):
    """Vue principale de l'assistant IA"""
    specialties = Specialty.objects.all()
    exemples = [
        'douleur poitrine palpitations essoufflement',
        'boutons rougeurs démangeaisons acné',
        'migraine vertiges troubles vision',
        'douleur dent gencive saignement',
        'fièvre toux rhinite enfant',
        'diarrhée nausée douleur abdomen',
        'yeux rouges larmoiement vision floue',
        'douleur genou dos entorse',
        'règles irrégulières douleur pelvienne',
        'oreille douleur surdité acouphène',
        'brûlure estomac reflux constipation',
        'urine fréquente douleur rein',
    ]
    return render(request, 'ai_orientation/suggest.html', {
        'specialties': specialties,
        'exemples': exemples,
    })


def ai_api(request):
    """API JSON pour le chatbot IA"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        symptoms = data.get('symptoms', '')

        if not symptoms:
            return JsonResponse({'error': 'Veuillez décrire vos symptômes.'}, status=400)

        result = suggest_specialty(symptoms)
        urgency = classify_urgency(symptoms)

        # Résumé automatique du motif
        summary = auto_summarize(symptoms)

        # Médecins recommandés
        recommended_doctors = []
        if result['specialty']:
            doctors = Doctor.objects.filter(
                specialty__name__icontains=result['specialty'],
                is_active=True
            ).order_by('-rating')[:3]
            recommended_doctors = [
                {
                    'id': d.pk,
                    'name': str(d),
                    'specialty': d.specialty.name if d.specialty else '',
                    'rating': float(d.rating),
                    'experience': d.years_experience,
                }
                for d in doctors
            ]

        return JsonResponse({
            'specialty': result['specialty'],
            'confidence': result['confidence'],
            'alternatives': result['alternatives'],
            'urgency': urgency,
            'urgency_label': {'low': 'Faible', 'medium': 'Modérée', 'high': 'Élevée'}.get(urgency, 'Faible'),
            'message': result['message'],
            'recommended_doctors': recommended_doctors,
            'summary': summary,
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def auto_summarize(symptoms_text):
    """
    Résumé automatique du motif de consultation en 1 phrase.
    Extrait les symptômes principaux et génère une phrase concise.
    """
    if not symptoms_text or len(symptoms_text.strip()) < 5:
        return symptoms_text

    text = symptoms_text.lower().strip()

    # Mots à ignorer
    stop_words = {
        'je', 'j', 'ai', 'me', 'mon', 'ma', 'mes', 'un', 'une', 'des', 'le', 'la',
        'les', 'de', 'du', 'et', 'ou', 'en', 'au', 'aux', 'sur', 'par', 'que',
        'qui', 'depuis', 'parfois', 'souvent', 'aussi', 'très', 'assez', 'il', 'elle',
        'resens', 'ressens', 'sens', 'sent', 'suis', 'avoir', 'avoir', 'niveau',
        'niveau', 'fois', 'peu', 'beaucoup', 'avec', 'sans', 'pour', 'dans'
    }

    # Extraire les mots significatifs
    words = [w.strip('.,!?;:') for w in text.split()]
    key_words = [w for w in words if w not in stop_words and len(w) > 3]

    # Limiter à 6 mots-clés max
    key_words = key_words[:6]

    if not key_words:
        return symptoms_text[:100]

    # Générer la phrase résumée
    if len(key_words) == 1:
        return f"Patient présentant : {key_words[0]}."
    elif len(key_words) <= 3:
        return f"Patient présentant : {', '.join(key_words[:-1])} et {key_words[-1]}."
    else:
        main = ', '.join(key_words[:3])
        secondary = ', '.join(key_words[3:])
        return f"Patient présentant principalement : {main}. Symptômes associés : {secondary}."


def predict_peak_slots(request):
    """
    Prédiction des créneaux les plus demandés.
    Analyse les RDV passés pour identifier les heures de pointe.
    """
    # Heures les plus demandées globalement
    hourly_stats = []
    for hour in range(7, 20):
        count = Appointment.objects.filter(time__hour=hour).count()
        hourly_stats.append({
            'hour': f'{hour:02d}h00',
            'count': count,
            'label': 'Très demandé' if count >= 5 else 'Demandé' if count >= 2 else 'Peu demandé'
        })

    # Trouver le pic
    if hourly_stats:
        peak = max(hourly_stats, key=lambda x: x['count'])
    else:
        peak = {'hour': '09h00', 'count': 0, 'label': 'Inconnu'}

    # Jours les plus demandés
    daily_stats = []
    day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for day_num in range(7):
        count = Appointment.objects.filter(date__week_day=day_num + 2).count()
        daily_stats.append({
            'day': day_names[day_num],
            'count': count,
        })

    return JsonResponse({
        'hourly_stats': hourly_stats,
        'daily_stats': daily_stats,
        'peak_hour': peak['hour'],
        'peak_count': peak['count'],
    })


def cancellation_analysis(request):
    """
    Analyse des annulations et absences par médecin et spécialité.
    """
    # Taux d'annulation par spécialité
    specialties_data = []
    for spec in Specialty.objects.all():
        total = Appointment.objects.filter(specialty=spec).count()
        cancelled = Appointment.objects.filter(specialty=spec, status='cancelled').count()
        absent = Appointment.objects.filter(specialty=spec, status='absent').count()
        if total > 0:
            specialties_data.append({
                'name': spec.name,
                'icon': spec.icon,
                'total': total,
                'cancelled': cancelled,
                'absent': absent,
                'taux_annulation': round((cancelled + absent) / total * 100, 1),
            })

    specialties_data.sort(key=lambda x: x['taux_annulation'], reverse=True)

    # Taux d'annulation par médecin
    doctors_data = []
    for doc in Doctor.objects.filter(is_active=True).select_related('user', 'specialty'):
        total = Appointment.objects.filter(doctor=doc).count()
        cancelled = Appointment.objects.filter(doctor=doc, status='cancelled').count()
        absent = Appointment.objects.filter(doctor=doc, status='absent').count()
        if total > 0:
            doctors_data.append({
                'name': str(doc),
                'specialty': doc.specialty.name if doc.specialty else '—',
                'total': total,
                'cancelled': cancelled,
                'absent': absent,
                'taux_annulation': round((cancelled + absent) / total * 100, 1),
            })

    doctors_data.sort(key=lambda x: x['taux_annulation'], reverse=True)

    # Stats globales
    total_all = Appointment.objects.count()
    total_cancelled = Appointment.objects.filter(status='cancelled').count()
    total_absent = Appointment.objects.filter(status='absent').count()
    taux_global = round((total_cancelled + total_absent) / total_all * 100, 1) if total_all > 0 else 0

    return JsonResponse({
        'specialties': specialties_data[:8],
        'doctors': doctors_data[:8],
        'global': {
            'total': total_all,
            'cancelled': total_cancelled,
            'absent': total_absent,
            'taux': taux_global,
        }
    })