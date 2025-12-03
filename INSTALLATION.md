# ============================================================================
# GUIDE D'INSTALLATION & DÉMARRAGE COMPLET
# ============================================================================

## 📋 Prérequis

- **Python** 3.10+ (vérifier : `python --version`)
- **pip** (gestionnaire de packages)
- **Git** (pour cloner le projet)
- **PostgreSQL** 12+ (optionnel, SQLite pour dev)

**Windows :** Télécharger depuis [python.org](https://python.org)  
**macOS :** `brew install python@3.11`  
**Linux (Ubuntu):** `sudo apt install python3.10 python3-pip`

---

## 🚀 Installation Étape par Étape

### 1. Cloner le projet
```bash
git clone https://github.com/votre-username/chantiers-api.git
cd chantiers-api
```

### 2. Créer l'environnement virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

✅ Vous devriez voir `(venv)` au début du prompt.

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

⏱️ Cela prend 2-3 minutes. Soyez patient !

### 4. Configurer les variables d'environnement
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres
# Les defaults fonctionnent pour développement
```

Contenu minimal de `.env` pour démarrage :
```
DEBUG=True
SECRET_KEY=your-super-secret-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Appliquer les migrations
```bash
python manage.py migrate
```

✅ Cela crée la base de données SQLite et les tables.

### 6. Créer un superutilisateur (admin)
```bash
python manage.py createsuperuser
```

Vous serez demandé de saisir :
- **Username** : `admin`
- **Email** : `admin@example.com`
- **Password** : Entrez un mot de passe sécurisé

### 7. Charger les données de test (optionnel)
```bash
python manage.py seed_data  # Si vous avez cette commande
```

Ou créer manuellement via Django admin.

### 8. Lancer le serveur de développement
```bash
python manage.py runserver
```

✅ Accédez à : **http://localhost:8000**

---

## 🔑 Accès à l'application

### Interface Admin Django
- URL : `http://localhost:8000/admin/`
- Username : `admin`
- Password : Le mot de passe que vous avez défini

### Documentation API (Swagger)
- URL : `http://localhost:8000/api/v1/schema/swagger/`

### API Browsable (DRF)
- URL : `http://localhost:8000/api/v1/chantiers/`

---

## 🧪 Tests

### Lancer les tests
```bash
pytest
```

### Tests spécifiques
```bash
# Tests du modèle Chantier
pytest chantiers/tests.py::TestChantierModel -v

# Tests API uniquement
pytest -k "API" -v

# Tests avec couverture
pytest --cov=chantiers --cov-report=html
```

---

## 📊 Créer des données de test

### Depuis Django Shell
```bash
python manage.py shell
```

Puis dans le shell :
```python
from chantiers.models import Chantier, Lot, Tache
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta

# Créer un utilisateur
chef = User.objects.create_user(username='chef1', password='pass123')

# Créer un chantier
chantier = Chantier.objects.create(
    numero='CH-TEST-001',
    nom='Rénovation Maison Test',
    adresse='123 rue de Test',
    codepostal='69000',
    ville='Lyon',
    date_debut=date.today(),
    date_fin_prevue=date.today() + timedelta(days=60),
    budget_total=Decimal('50000.00'),
    chef=chef
)

print(f"✅ Chantier créé : {chantier.numero}")
```

---

## 🐛 Dépannage Courant

### Erreur : "ModuleNotFoundError: No module named 'django'"
**Solution :** Activez le venv et installez les dépendances
```bash
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Erreur : "Port 8000 already in use"
**Solution :** Utilisez un autre port
```bash
python manage.py runserver 8001
```

### Erreur : "No migrations to apply"
**Solution :** Créez les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Base de données corrompue
**Solution :** Réinitialiser
```bash
# ⚠️ Attention : cela supprime TOUTES les données !
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### "Permission denied" sur Linux/Mac
**Solution :** Rendez le manage.py exécutable
```bash
chmod +x manage.py
```

---

## 🚢 Déploiement Production

### Préparation

1. **Installer Gunicorn**
```bash
pip install gunicorn
```

2. **Créer `.env` production**
```
DEBUG=False
SECRET_KEY=your-production-secret-key-very-long-and-random
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_ENGINE=postgresql
DB_NAME=chantiers_prod
DB_USER=chantiers_user
DB_PASSWORD=your-secure-password
DB_HOST=your-db-host
DB_PORT=5432
```

3. **Collecter les fichiers statiques**
```bash
python manage.py collectstatic --noinput
```

4. **Tester avec Gunicorn**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Sur Heroku

```bash
# 1. Créer l'app
heroku create your-app-name

# 2. Ajouter PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 3. Configurer les variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')

# 4. Déployer
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Sur Railway

```bash
# 1. Installer Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Créer un projet
railway init

# 4. Ajouter PostgreSQL
railway add

# 5. Déployer
railway up
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```bash
docker build -t chantiers-api .
docker run -p 8000:8000 --env-file .env chantiers-api
```

---

## 🔒 Sécurité Checklist

- [ ] `DEBUG=False` en production
- [ ] `SECRET_KEY` unique et sécurisé (50+ caractères aléatoires)
- [ ] HTTPS forcé (`SECURE_SSL_REDIRECT=True`)
- [ ] CORS configuré correctement (`CORS_ALLOWED_ORIGINS`)
- [ ] Base de données sécurisée (mot de passe fort)
- [ ] Backups réguliers
- [ ] Monitoring actif (Sentry, NewRelic)
- [ ] Logs centralisés

---

## 📚 Ressources Utiles

- [Django Official Docs](https://docs.djangoproject.com/)
- [DRF Docs](https://www.django-rest-framework.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [drf-spectacular (Swagger)](https://drf-spectacular.readthedocs.io/)
- [pytest-django](https://pytest-django.readthedocs.io/)

---

## 🤝 Support

Pour l'aide :
1. Consultez la documentation dans `/docs`
2. Ouvrez une issue GitHub
3. Consultez les tests existants

---

## 📝 Notes pour Débutants

**Structure Django :**
- `manage.py` = Interface de commande
- `config/` = Configuration globale
- `chantiers/` = Application métier
- `models.py` = Structure BD
- `views.py` = Logique API
- `serializers.py` = Conversion JSON
- `tests.py` = Tests unitaires

**Commandes utiles :**
```bash
python manage.py createsuperuser      # Ajouter un admin
python manage.py makemigrations        # Préparer changements BD
python manage.py migrate              # Appliquer changements BD
python manage.py shell                # Shell Python interactif
python manage.py dbshell              # Shell base de données
```

Bon développement ! 🚀
