"""Configuration for the fleet application."""

from django.apps import AppConfig


class FleetConfig(AppConfig):
    """Application configuration for Fleet."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fleet"

    def ready(self):
        """Connect application signals."""

        import fleet.signals  # Importa y conecta las señales
