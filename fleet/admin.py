# fleet/admin.py
from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'year', 'status', 'soat_due_date', 'rtm_due_date')
    search_fields = ('plate', 'vin', 'brand', 'model')
    list_filter = ('status', 'fuel_type', 'brand')