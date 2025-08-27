# inventory/admin.py
from django.contrib import admin
from .models import Supplier, Part, InventoryMovement

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'nit', 'contact_person')

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'stock_current', 'stock_min', 'average_cost', 'supplier')
    search_fields = ('sku', 'name')
    list_filter = ('supplier',)

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('part', 'movement_type', 'quantity', 'timestamp', 'work_order')
    list_filter = ('movement_type', 'timestamp')