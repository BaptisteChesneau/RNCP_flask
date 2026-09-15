# 🏢 ML2C CONSEIL — Plateforme Web & Chatbot Intelligent

> Application web full-stack développée pour le cabinet d'expertise comptable **ML2C CONSEIL**. Elle intègre un tableau de bord administrateur sécurisé, un espace client, un module de demande de devis avec prise de rendez-vous interactive, ainsi qu'un chatbot d'assistance.

---

## 📋 Table des matières

- [À propos du projet](#-à-propos-du-projet)
- [Fonctionnalités principales](#-fonctionnalités-principales)
- [Architecture & Technologies](#-architecture--technologies)
- [Structure du Projet](#-structure-du-projet)
- [Installation & Configuration](#-installation--configuration)
- [Lancement de l'application](#-lancement-de-lappllication)
- [Tests & Validation (`pytest`)](#-tests--validation-pytest)
- [Déploiement](#-déploiement)

---

## 💡 À propos du projet

Dans le cadre de la modernisation des services du cabinet **ML2C CONSEIL**, ce projet vise à offrir :
1. Une vitrine digitale élégante et ergonomique pour les clients du cabinet.
2. Un module de demande de devis personnalisé avec calendrier interactif 3D pour réserver un créneau d'entretien.
3. Un espace d'administration sécurisé (Niveau 3 / Super Admin) pour suivre l'activité, gérer les comptes clients et consulter les logs système.
4. Un chatbot intelligent permettant de répondre aux questions fréquentes des clients.

---

## 🚀 Fonctionnalités principales

- 🔐 **Authentification & Sécurité :**
  - Connexion sécurisée avec gestion des sessions Flask.
  - Espace Administrateur protégé avec contrôle du nombre de tentatives, limitation de session à 30 min et journalisation dynamique des logs.
  - Protection contre les injections SQL et failles XSS.

- 💼 **Demande de Devis & Rendez-vous :**
  - Formulaire multi-étapes (Informations, Sélection du service, Prise de rendez-vous).
  - Calendrier interactif avec sélection dynamique des créneaux horaires (Matin / Après-midi).
  - Récapitulatif en temps réel de la demande.

- 💬 **Support & Communication :**
  - Chatbot interactif dédié au support client ML2C.
  - API de messagerie interne pour échanger entre clients et collaborateurs.

---

## 🛠 Architecture & Technologies

- **Backend :** Python 3.12, Flask, Flask-SQLAlchemy, Flask-Limiter
- **Frontend :** HTML5, CSS3 (Variables CSS, Flexbox/Grid, animations 3D), JavaScript (ES6+), Bootstrap 4, FontAwesome 6
- **Bases de données (Hybride) :**
  - **PostgreSQL / SQLite :** Données relationnelles (Utilisateurs, Devis, Rendez-vous, Messages).
  - **MongoDB :** Stockage des logs et de l'historique des conversations du Chatbot.
- **Tests Unitaires & d'Intégration :** Pytest (avec BDD SQLite `:memory:` pour l'isolation des tests).

---

## 📁 Structure du Projet

```text
RNCP_FLASK/
├── api/                       # Endpoints d'API (Messages, Chatbot, etc.)
│   ├── messages_api.py
│   └── ...
├── models/                    # Modèles SQLAlchemy & Schemas MongoDB
│   ├── message.py
│   └── user.py
├── static/                    # Fichiers statiques (CSS, JS, Images)
│   ├── css/
│   └── js/
├── templates/                 # Templates Jinja2 (HTML)
│   ├── admin_login.html
│   ├── devis.html
│   ├── header.html
│   └── footer.html
├── tests/                     # Suite de tests Pytest
│   ├── fonctionnel/           # Tests fonctionnels des parcours clients
│   ├── integration/           # Tests d'intégration (BDD, Modèles, Routes, Sécurité)
│   ├── test_api/              # Tests des API JSON
│   └── unit/                  # Tests unitaires
├── app.py                     # Point d'entrée principal de l'application Flask
├── extensions.py              # Initialisation des extensions Flask (db, etc.)
├── requirements.txt           # Dépendances Python
└── README.md                  # Documentation du projet

⚙️ Installation & Configuration
1. Prérequis
Python 3.10+

Git

2. Cloner le projet
Bash
git clone <URL_DU_DEPOT_GIT>
cd RNCP_flask
3. Créer et activer un environnement virtuel
Bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# Windows (Git Bash / Linux / Mac)
python -m venv venv
source venv/bin/activate
4. Installer les dépendances
Bash
pip install -r requirements.txt
🎯 Lancement de l'application
Pour exécuter le serveur de développement local :

Bash
python app.py
L'application sera accessible sur votre navigateur à l'adresse : http://127.0.0.1:5000/

🧪 Tests & Validation (pytest)
Le projet intègre une couverture de tests automatisés vérifiant le bon fonctionnement des modèles, des accès sécurisés, des API et des flux utilisateurs.

Pour exécuter l'ensemble de la suite de tests :

Bash
# Lancement classique
python -m pytest

# Lancement en mode détaillé (verbose)
python -m pytest -v
Note : Les tests s'exécutent sur une base de données SQLite temporaire en mémoire (sqlite:///:memory:), garantissant l'absence d'impact sur la base de données de développement ou de production.

🚀 Déploiement
L'application est configurée pour être déployée sur la plateforme PaaS Scalingo.

Variables d'environnement requises sur Scalingo :

FLASK_ENV=production

SECRET_KEY=<VOTRE_CLE_SECRETE>

DATABASE_URL=<URL_POSTGRESQL>