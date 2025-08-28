"""Configuration for the inventory application."""

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Application configuration for Inventory."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
