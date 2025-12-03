# ============================================================================
# Django Settings - Configuration Centrale
# Environnement : DEVELOPMENT (adapter pour PRODUCTION dans .env)
# ============================================================================

import os
from pathlib import Path
from datetime import timedelta
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# ============================================================================
# CHEMINS & RÉPERTOIRES
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# ============================================================================
# SÉCURITÉ & CLÉS
# ============================================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Sécurité en production
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}

# ============================================================================
# APPLICATIONS INSTALLÉES
# ============================================================================
INSTALLED_APPS = [
    # Django natives
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Packages tiers
    'rest_framework',                    # Django REST Framework
    'rest_framework.authtoken',          # Token Authentication
    'corsheaders',                       # CORS support
    'django_filters',                    # Filtrage avancé
    'drf_spectacular',                   # Documentation Swagger/OpenAPI
    'django_extensions',                 # Commandes django supplémentaires
    
    # Notre application
    'chantiers.apps.ChantiersConfig',
]

# ============================================================================
# MIDDLEWARE
# ============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',              # CORS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================================
# CORS - Configuration pour l'API mobile
# ============================================================================
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

# ============================================================================
# BASE DE DONNÉES
# ============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql' if os.getenv('DB_ENGINE') == 'postgresql' else 'django.db.backends.sqlite3',
        'NAME': os.getenv('DB_NAME', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# ============================================================================
# DJANGO REST FRAMEWORK - Configuration API
# ============================================================================
REST_FRAMEWORK = {
    # Authentification
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Permissions par défaut
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Filtrage
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    # Format d'affichage
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    
    # Documentation
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================================================
# DRF SPECTACULAR - Documentation Swagger/OpenAPI
# ============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Gestion des Chantiers',
    'DESCRIPTION': 'API REST pour la gestion complète des chantiers, équipes et suivi terrain',
    'VERSION': '1.0.0',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'AUTHENTICATION_PATTERNS': [
        r'^api/v1/',
    ],
    'PREPROCESSING_HOOKS': [
        'chantiers.schema_hooks.preprocessing_filter_hook',
    ],
}

# ============================================================================
# AUTHENTIFICATION
# ============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================================
# INTERNATIONALISATION
# ============================================================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ============================================================================
# LOGGING - Configuration des logs
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'chantiers': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ============================================================================
# TEMPLATES
# ============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================================================
# URL Configuration
# ============================================================================
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ============================================================================
# STOCKAGE DE FICHIERS
# ============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# S3 / Stockage cloud (optionnel, pour production)
if os.getenv('USE_S3') == 'True':
    import boto3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'eu-west-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# ============================================================================
# CONFIGURATION MÉTIER
# ============================================================================
CHANTIERS_CONFIG = {
    'MAX_PHOTO_SIZE': 5 * 1024 * 1024,  # 5 MB
    'ALLOWED_PHOTO_FORMATS': ['jpg', 'jpeg', 'png', 'webp'],
    'MAX_PHOTOS_PER_TACHE': 50,
    'AUTO_GEOCODING': os.getenv('AUTO_GEOCODING', 'False') == 'True',
}

# ============================================================================
# CACHE (optionnel)
# ============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'chantiers-cache',
    }
}

# Créer les répertoires nécessaires au démarrage
for directory in [MEDIA_ROOT, os.path.join(BASE_DIR, 'logs')]:
    os.makedirs(directory, exist_ok=True)
