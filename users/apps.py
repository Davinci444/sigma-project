"""Configuration for the users application."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Application configuration for Users."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
