# workorders/apps.py
from django.apps import AppConfig

class WorkordersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "workorders"

    def ready(self):
        # Importa señales definidas en models (costos, activación plan) y las extra
        import workorders.models  # noqa
        import workorders.signals_extra  # noqa
