"""Admin configuration for inventory (incluye repuestos por vehículo)."""
from django.contrib import admin
from .models import (
    Supplier, Part, InventoryMovement,
    SpareCategory, SpareItem, VehicleSpare
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "email")
    search_fields = ("name", "nit", "contact_person")


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "quantity", "unit", "supplier")
    search_fields = ("sku", "name")
    list_filter = ("supplier",)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "movement_type", "part", "quantity", "work_order")
    list_filter = ("movement_type", "timestamp")
    search_fields = ("part__sku", "part__name", "work_order__id")


@admin.register(SpareCategory)
class SpareCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SpareItem)
class SpareItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "category__name")
    autocomplete_fields = ("category",)


@admin.register(VehicleSpare)
class VehicleSpareAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "spare_item", "brand", "part_number", "quantity", "last_replacement_date")
    list_filter = ("spare_item__category",)
    search_fields = ("vehicle__plate", "spare_item__name", "brand", "part_number")
    autocomplete_fields = ("vehicle", "spare_item")
