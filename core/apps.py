"""Configuration for the core application."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Application configuration for Core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
