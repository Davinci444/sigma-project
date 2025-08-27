# project/settings.py (Versión final para Render)

import os
from pathlib import Path
import dj_database_url # Importamos la herramienta para la base de datos

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURACIONES DE SEGURIDAD IMPORTANTES ---
# Leemos la SECRET_KEY desde las variables de entorno de Render. ¡Mucho más seguro!
SECRET_KEY = os.environ.get('SECRET_KEY')

# DEBUG debe ser Falso (False) en producción para no mostrar errores sensibles.
# Lo leemos de una variable de entorno. Si no existe, por seguridad será Falso.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Los dominios permitidos. Leemos la variable de Render que creamos.
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(' ')


# --- DEFINICIÓN DE APLICACIONES ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps de Terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Nuestras Apps Locales
    'core.apps.CoreConfig',
    'fleet.apps.FleetConfig',
    'inventory.apps.InventoryConfig',
    'reports.apps.ReportsConfig',
    'users.apps.UsersConfig',
    'workorders.apps.WorkordersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise debe ir aquí, justo después del SecurityMiddleware
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
        'DIRS': [],
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


# --- CONFIGURACIÓN DE LA BASE DE DATOS PARA RENDER ---
# Esta configuración usa la URL de la base de datos que Render nos da automáticamente.
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )
}


# --- VALIDACIÓN DE CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- CONFIGURACIÓN INTERNACIONAL ---
LANGUAGE_CODE = 'es-co' # Español de Colombia
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# --- CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS (CSS, JS) ---
STATIC_URL = 'static/'
# Le decimos a Django que junte todos los archivos estáticos en una carpeta llamada 'staticfiles'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuración de WhiteNoise para que pueda servir estos archivos de forma eficiente
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- CONFIGURACIÓN DE LLAVE PRIMARIA POR DEFECTO ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURACIÓN DE DJANGO REST FRAMEWORK (API) ---
REST_FRAMEWORK = {
    # Por defecto, solo usuarios autenticados podrán acceder a la API.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Usaremos JSON Web Tokens (JWT) para la autenticación.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}