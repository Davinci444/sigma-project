# project/settings.py (Versión final para Render y Desarrollo Local)

import os
from pathlib import Path
import dj_database_url

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURACIONES DE SEGURIDAD INTELIGENTES ---

# Leemos la variable de entorno 'RENDER', que solo existe en Render.
IS_PRODUCTION = os.environ.get('RENDER') == 'true'

if IS_PRODUCTION:
    # --- CONFIGURACIÓN DE PRODUCCIÓN (EN RENDER) ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(' ')
else:
    # --- CONFIGURACIÓN DE DESARROLLO (EN TU PC) ---
    SECRET_KEY = 'django-insecure-ESTA-LLAVE-ES-SOLO-PARA-DESARROLLO-LOCAL'
    DEBUG = True
    ALLOWED_HOSTS = ['*'] # Permitimos todo para pruebas locales

# --- DEFINICIÓN DE APLICACIONES ---
# (Esta sección no cambia)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'core.apps.CoreConfig',
    'fleet.apps.FleetConfig',
    'inventory.apps.InventoryConfig',
    'reports.apps.ReportsConfig',
    'users.apps.UsersConfig',
    'workorders.apps.WorkordersConfig',
]

# (Esta sección no cambia)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # --- MODIFICACIÓN AQUÍ ---
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# --- CONFIGURACIÓN DE LA BASE DE DATOS (INTELIGENTE) ---
if IS_PRODUCTION:
    # En Render, usamos la base de datos PostgreSQL de la URL de entorno.
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # En tu PC, usamos un archivo de base de datos local simple (SQLite).
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# (El resto del archivo no cambia)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURACIÓN DE DJANGO REST FRAMEWORK (API) ---
# (Añadimos esta sección que faltaba del paso anterior)
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}