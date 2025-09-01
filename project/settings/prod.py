from .base import *  # noqa
import os
import dj_database_url

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', '').lower() == 'true'
ALLOWED_HOSTS = [h for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}
