# workorders/apps.py
from django.apps import AppConfig

class WorkordersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workorders'

    # --- NUEVO: Registramos las señales al iniciar la app ---
    def ready(self):
        import workorders.models # Importa los modelos donde están las señales
