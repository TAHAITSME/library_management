# Django Settings für Production (optionnel)

# À utiliser UNIQUEMENT en production
# Ne pas ignorer les avertissements de sécurité!

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# En production, utiliser une variable d'environnement
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

# En production, utiliser une vraie base de données
# Exemple PostgreSQL:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'library_db',
#         'USER': 'postgres',
#         'PASSWORD': 'password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
