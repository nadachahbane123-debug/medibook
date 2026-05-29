# ⚕ MediBook — Plateforme de Gestion de Rendez-vous Médicaux

> Projet de fin de module Django · EMI Rabat · Année universitaire 2025–2026

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue)

## 📋 Description

MediBook est une plateforme web complète de gestion de rendez-vous médicaux développée avec Django. Elle permet aux patients de rechercher des médecins, consulter leurs disponibilités et réserver des rendez-vous, aux médecins de gérer leur planning, et aux administrateurs de superviser la plateforme.

## ✨ Fonctionnalités

### Utilisateurs & Rôles
- 4 rôles : visiteur, patient, médecin, administrateur
- Inscription patient, connexion/déconnexion
- **Réinitialisation de mot de passe par email**
- Profil enrichi (photo, groupe sanguin, allergies, antécédents)

### Médecins & Spécialités
- 12 spécialités médicales (cardiologie, ORL, dermatologie...)
- Profils médecins complets (photo, bio, tarif, expérience)
- Recherche avancée (note min, tarif max, expérience, tri)
- Pagination 9 médecins/page

### Rendez-vous
- Réservation avec sélection de créneaux dynamique (AJAX)
- **Modification de rendez-vous** (changement date/heure)
- Annulation avec raison (jusqu'à 2h avant)
- 5 statuts : en attente / confirmé / annulé / terminé / absent
- Classification automatique de l'urgence (faible/modérée/élevée)
- Compte-rendu médical (diagnostic, traitement, ordonnance)
- Système d'avis étoiles (1-5)

### Tableaux de bord
- **Patient** : prochains RDV, historique, notifications, export PDF
- **Médecin** : planning du jour, semaine, **calendrier hebdomadaire visuel**, graphique mensuel
- **Admin** : statistiques globales, gestion médecins, **statistiques IA**, graphiques Chart.js

### Intelligence Artificielle
- Chatbot d'orientation médicale interactif
- Algorithme TF-IDF + similarité cosinus (scikit-learn)
- 12 spécialités dans la base de connaissances
- Classification d'urgence automatique
- Médecins recommandés selon la suggestion

### Fonctionnalités techniques
- Notifications temps réel (polling JS 30s)
- **Export PDF** des rendez-vous et historique patient
- **Rappels automatiques** (`python manage.py send_reminders`)
- Pages 404/500 personnalisées
- 38+ tests unitaires

## 🚀 Lancement rapide

### Prérequis
- Docker & Docker Compose

```bash
# 1. Cloner le repo
git clone https://github.com/votre-username/medibook.git
cd medibook

# 2. Copier le .env
cp .env .env.local  # modifiez les variables si besoin

# 3. Lancer
docker compose up -d --build

# 4. Créer un superuser
docker compose exec web python manage.py createsuperuser

# 5. Ouvrir http://localhost:8000
```

### Variables d'environnement (.env)

```env
SECRET_KEY=votre-clé-secrète
DJANGO_DEBUG=1
MYSQL_DATABASE=medibook_db
MYSQL_USER=medibook_user
MYSQL_PASSWORD=votre-mot-de-passe
MYSQL_ROOT_PASSWORD=root-password
MYSQL_HOST=db
MYSQL_PORT=3306
```

## 🗄️ Base de données

MySQL 8.0 via Docker Compose. Les migrations sont appliquées automatiquement au démarrage. Les 12 spécialités médicales sont créées automatiquement par `entrypoint.sh`.

## 🧪 Tests

```bash
docker compose exec web python manage.py test --verbosity=2
```

## 🏗️ Architecture

```
medibook/
├── accounts/          # Utilisateurs, authentification, rôles
├── patients/          # Profils patients
├── doctors/           # Médecins, spécialités
├── appointments/      # Rendez-vous, avis, consultations
├── schedules/         # Disponibilités, créneaux
├── dashboard/         # Tableaux de bord
├── ai_orientation/    # IA TF-IDF + cosine similarity
├── notifications/     # Système de notifications
├── templates/         # Templates HTML
├── static/            # CSS, JS
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```

## 🔒 Sécurité

- CSRF activé sur tous les formulaires
- Pages protégées par `@login_required`
- Contrôle d'accès par rôle (patient/médecin/admin)
- Mots de passe hashés par Django
- Variables sensibles dans `.env` (ne jamais commiter)
- Mode DEBUG désactivé en production

## 📦 Technologies

| Composant | Technologie |
|-----------|-------------|
| Backend | Django 5.2 |
| Base de données | MySQL 8.0 |
| IA | scikit-learn (TF-IDF + cosine) |
| Frontend | Django Templates + CSS custom |
| Graphiques | Chart.js |
| Conteneurisation | Docker + Docker Compose |
| Serveur WSGI | Gunicorn |
| Fichiers statiques | WhiteNoise |
| CI/CD | GitHub Actions |

## 👩‍💻 Auteur

Projet réalisé dans le cadre du module **Développement Web avec Django** — EMI Rabat — 2025/2026
