"""Configuration for the workorders application."""

from django.apps import AppConfig


class WorkordersConfig(AppConfig):
    """Application configuration for Workorders."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "workorders"

    # --- NUEVO: Registramos las señales al iniciar la app ---
    def ready(self):
        """Import signals when the app is ready."""

        import workorders.models  # Importa los modelos donde están las señales
