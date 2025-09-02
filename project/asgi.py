"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Selecciona el módulo de settings según la variable de entorno
env = os.environ.get('DJANGO_ENV', 'prod')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'project.settings.{env}')

application = get_asgi_application()
