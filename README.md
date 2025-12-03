# Gestion Complète des Chantiers - API Django REST

Plateforme production-ready pour la gestion et le suivi de chantiers en temps réel avec API mobile, gestion d'équipes, sous-traitants et documentation photographique.

## 🎯 Fonctionnalités Principales

### 1. **Gestion des Chantiers**
- Création et suivi des chantiers (adresse, dates, budget, status)
- Division en lots (phases de travail)
- Subdivision en tâches (travaux détaillés)
- Suivi des heures passées par équipe/tâche
- États : En attente → En cours → En pause → Terminé → Facturé

### 2. **Gestion des Équipes & Sous-Traitants**
- Équipes internes avec rôles (Chef, Ouvrier, Apprenti)
- Sous-traitants externes avec spécialités
- Attribution flexible des ressources par tâche
- Suivi des heures par personne

### 3. **Suivi Terrain**
- API pour saisir l'avancement depuis mobile
- Upload de photos géolocalisées
- Remarques et signalements d'anomalies
- Validation par chef de chantier

### 4. **API REST Complète**
- Django REST Framework (DRF)
- Filtrage, recherche, pagination
- Token Authentication (Bearer token)
- Permissions granulaires
- Documentation Swagger intégrée

## 🚀 Stack Technologique

- **Backend** : Django 4.2+ avec Django REST Framework
- **Base de données** : PostgreSQL (SQLite dev)
- **Authentication** : Token + JWT (optionnel)
- **Upload fichiers** : Pillow + django-storages (S3 ready)
- **Filtrage** : django-filter
- **Documentation** : drf-spectacular (Swagger/OpenAPI)
- **Monitoring** : python-dotenv + logging
- **Tests** : pytest + pytest-django

## 📋 Prérequis

- Python 3.10+
- pip ou Poetry
- PostgreSQL 12+ (optionnel, SQLite pour développement)
- Git

## ⚙️ Installation Rapide

```bash
# 1. Cloner et entrer dans le projet
git clone https://github.com/votre-username/chantiers-api.git
cd chantiers-api

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Copier le fichier d'env et le configurer
cp .env.example .env
# Éditer .env avec vos paramètres

# 5. Créer la base de données
python manage.py migrate

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver

# 8. Accéder à l'API
# Admin : http://localhost:8000/admin
# API Swagger : http://localhost:8000/api/schema/swagger/
# API Browsable : http://localhost:8000/api/v1/
```

## 📚 Documentation API

### Endpoints Principaux

#### Chantiers
```
GET    /api/v1/chantiers/               - Lister tous les chantiers
POST   /api/v1/chantiers/               - Créer un chantier
GET    /api/v1/chantiers/{id}/          - Détails d'un chantier
PATCH  /api/v1/chantiers/{id}/          - Mettre à jour un chantier
DELETE /api/v1/chantiers/{id}/          - Supprimer un chantier
```

#### Tâches
```
GET    /api/v1/taches/                  - Lister les tâches
POST   /api/v1/taches/                  - Créer une tâche
GET    /api/v1/taches/{id}/             - Détails d'une tâche
PATCH  /api/v1/taches/{id}/             - Mettre à jour une tâche
POST   /api/v1/taches/{id}/ajouter_photo/ - Ajouter une photo
```

#### Équipes & Membres
```
GET    /api/v1/equipes/                 - Lister les équipes
POST   /api/v1/equipes/                 - Créer une équipe
GET    /api/v1/membres/                 - Lister les membres
POST   /api/v1/membres/                 - Ajouter un membre
```

#### Suivi des Heures
```
GET    /api/v1/heures_travail/          - Lister les entrées d'heures
POST   /api/v1/heures_travail/          - Enregistrer des heures
GET    /api/v1/chantiers/{id}/rapport/  - Rapport d'avancement
```

### Exemple de Requête

```bash
# Créer un chantier
curl -X POST http://localhost:8000/api/v1/chantiers/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Rénovation Maison Martin",
    "adresse": "123 rue de la Paix, Lyon",
    "date_debut": "2024-01-15",
    "date_fin_prevue": "2024-06-30",
    "budget_total": 50000.00,
    "description": "Rénovation complète"
  }'

# Récupérer les tâches avec filtrage
curl -X GET "http://localhost:8000/api/v1/taches/?chantier_id=1&status=EN_COURS" \
  -H "Authorization: Token YOUR_TOKEN"
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=chantiers

# Tests spécifiques
pytest chantiers/tests.py::test_creer_chantier -v
```

## 📱 Intégration Mobile

L'API est conçue pour être consommée par une app mobile (React Native, Flutter) :
- Upload de photos avec géolocalisation
- Synchronisation hors-ligne supportée
- Pagination optimisée pour mobile
- Format JSON léger

Voir `docs/MOBILE_INTEGRATION.md` pour les détails.

## 🔐 Sécurité

- ✅ Token Authentication (Bearer)
- ✅ CORS configuré
- ✅ Rate Limiting
- ✅ Validation des entrées
- ✅ Permissions par rôle
- ✅ Logs d'audit

## 🚢 Déploiement Production

### Docker

```dockerfile
# Voir Dockerfile à la racine
docker build -t chantiers-api .
docker run -p 8000:8000 --env-file .env chantiers-api
```

### Heroku / Railway / DigitalOcean

```bash
# Configuration pour Procfile ou Railway
# Voir docs/INSTALLATION.md
```

## 📊 Modèles de Données

```
Chantier
  ├─ Lot (phases du chantier)
  │   └─ Tâche (travaux détaillés)
  │       ├─ HeureTravail (suivi d'heures)
  │       └─ PhotoRapport (documentation)
  ├─ Équipe
  │   └─ Membre (Chef, Ouvrier, Apprenti)
  └─ SousTraitant (prestataires externes)
```

## 🛠️ Développement

### Créer une nouvelle migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Shell Django interactif
```bash
python manage.py shell
```

### Créer des données de test
```bash
python manage.py seed_data  # Fixture personnalisée
```

## 📦 Structure du Projet Complète

Voir `structure_projet.txt` pour l'arborescence détaillée.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/NomFeature`)
3. Commit les changements (`git commit -m 'Add feature'`)
4. Push vers la branche (`git push origin feature/NomFeature`)
5. Ouvrir une Pull Request

## 📝 License

MIT License - voir LICENSE.md

## 📞 Support

Pour les questions :
- Ouvrir une issue GitHub
- Consulter la documentation dans `/docs`
- Contacter : dev@chantiers-api.com

---

**Dernière mise à jour** : Décembre 2024  
**Version** : 1.0.0  
**Statut** : Production Ready ✅
