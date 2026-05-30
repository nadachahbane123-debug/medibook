# ⚕ MediBook — Plateforme de Gestion de Rendez-vous Médicaux

> Projet de fin de module Django · EMI Rabat · Année universitaire 2025–2026

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-brightgreen)

## 📋 Description

MediBook est une plateforme web complète de gestion de rendez-vous médicaux développée avec Django. Elle permet aux patients de rechercher des médecins, consulter leurs disponibilités et réserver des rendez-vous, aux médecins de gérer leur planning, et aux administrateurs de superviser la plateforme.

🌐 **Application déployée** : http://84.8.221.206:8121/

## ✨ Fonctionnalités

### Utilisateurs & Rôles
- 4 rôles : visiteur, patient, médecin, administrateur
- Inscription patient, connexion/déconnexion
- Réinitialisation et modification de mot de passe
- Profil enrichi (photo, groupe sanguin, allergies, antécédents)

### Médecins & Spécialités
- 12 spécialités médicales (cardiologie, ORL, dermatologie...)
- Profils médecins complets (photo, bio, tarif, expérience, statut actif/inactif)
- Recherche avancée (note min, tarif max, expérience, tri)
- Pagination 9 médecins/page

### Rendez-vous
- Réservation avec sélection de créneaux dynamique (AJAX)
- Modification de rendez-vous (changement date/heure)
- Annulation avec raison (jusqu'à 2h avant)
- 5 statuts : en attente / confirmé / annulé / terminé / absent
- Classification automatique de l'urgence (faible/modérée/élevée)
- Compte-rendu médical (diagnostic, traitement, ordonnance)
- **Ordonnance PDF** générée automatiquement
- Système d'avis étoiles (1-5)

### Tableaux de bord
- **Patient** : prochains RDV, RDV passés, annulés, profil médical, notifications, export PDF
- **Médecin** : planning du jour, semaine, calendrier hebdomadaire visuel, graphique mensuel, 8 statistiques
- **Admin** : statistiques globales, gestion médecins/utilisateurs/spécialités, statistiques IA, graphiques Chart.js

### Intelligence Artificielle 🤖
- Chatbot d'orientation médicale interactif (TF-IDF + cosine similarity)
- 12 spécialités dans la base de connaissances avec règles directes prioritaires
- Classification d'urgence automatique (faible/modérée/élevée)
- Médecins recommandés selon la suggestion IA
- **Résumé automatique** du motif de consultation
- **Prédiction des créneaux** les plus demandés (heures de pointe)
- **Analyse des annulations** et absences par médecin/spécialité

### Messagerie & Notifications
- Messagerie interne patient ↔ médecin
- Notifications temps réel (polling JS 30s)
- Rappels automatiques (`python manage.py send_reminders`)

### Fonctionnalités techniques
- Export PDF des rendez-vous et historique patient
- Pages 404/500 personnalisées
- Recherche globale (médecins + spécialités)
- Gestion des disponibilités avec jours de congé
- 45 tests unitaires automatisés

## 🚀 Lancement rapide

### Prérequis
- Docker & Docker Compose

```bash
# 1. Cloner le repo
git clone https://github.com/nadachahbane123-debug/medibook.git
cd medibook

# 2. Lancer
docker compose up -d --build

# 3. Créer un superuser
docker compose exec web python manage.py createsuperuser

# 4. Ouvrir http://localhost:8000
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
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🗄️ Base de données

MySQL 8.0 via Docker Compose. Les migrations sont appliquées automatiquement au démarrage. Les 12 spécialités médicales sont créées automatiquement par `entrypoint.sh`.

## 🧪 Tests

```bash
docker compose exec web python manage.py test --verbosity=2
# 45 tests — OK
```

## 🏗️ Architecture
medibook/
├── accounts/          # Utilisateurs, authentification, rôles
├── patients/          # Profils patients
├── doctors/           # Médecins, spécialités
├── appointments/      # Rendez-vous, avis, consultations, PDF
├── schedules/         # Disponibilités, créneaux, jours de congé
├── dashboard/         # Tableaux de bord (patient/médecin/admin)
├── ai_orientation/    # IA TF-IDF + cosine similarity
├── notifications/     # Système de notifications
├── messaging/         # Messagerie interne
├── templates/         # Templates HTML
├── static/            # CSS, JS
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci-cd.yml

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
| IA | scikit-learn (TF-IDF + cosine similarity) |
| Frontend | Django Templates + CSS custom |
| Graphiques | Chart.js |
| PDF | WeasyPrint / ReportLab |
| Conteneurisation | Docker + Docker Compose |
| Serveur WSGI | Gunicorn |
| Fichiers statiques | WhiteNoise |
| CI/CD | GitHub Actions + Docker Hub |
| Déploiement | Dokploy (Cloud VM) |

## 🌐 Déploiement

L'application est déployée sur une machine virtuelle Cloud via **Dokploy** :

- **URL** : http://84.8.221.206:8121/
- **Image Docker Hub** : `nxdx/medibook:latest`
- **CI/CD** : Push sur `main` → Tests → Build → Push Docker Hub automatique

## 👩‍💻 Auteures

**Nada CHAHBANE** & **Ihssane AMADOUR**
Étudiantes en Modélisation Informatique Scientifique — EMI Rabat
Module : Développement Web avec Django — 2025/2026