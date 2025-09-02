"""Configuration for the core application."""

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.management import call_command


class CoreConfig(AppConfig):
    """Application configuration for Core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Seed default maintenance manuals after migrations."""

        def seed_manuals(sender, **kwargs):
            # Fallback seeding in case command isn't run manually
            try:
                call_command("seed_manuals", verbosity=0)
            except Exception:
                pass

        post_migrate.connect(seed_manuals, sender=self)
