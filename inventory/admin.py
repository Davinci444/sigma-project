"""Admin configuration for inventory models."""

from django.contrib import admin
from .models import Supplier, Part, InventoryMovement


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin interface for suppliers."""

    list_display = ("name", "contact_person", "phone", "email")
    search_fields = ("name", "nit", "contact_person")


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    """Admin interface for parts."""

    # --- AÑADIMOS 'unit' A LA VISTA ---
    list_display = ("sku", "name", "unit", "stock_current", "stock_min", "supplier")
    search_fields = ("sku", "name")
    list_filter = ("supplier", "unit")  # <-- Y a los filtros


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    """Admin interface for inventory movements."""

    list_display = ("part", "movement_type", "quantity", "timestamp", "work_order")
    list_filter = ("movement_type", "timestamp")

