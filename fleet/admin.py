# fleet/admin.py (Versión Corregida)
from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    # Añadimos los nuevos campos de odómetro
    list_display = ('plate', 'brand', 'model', 'current_odometer_km', 'odometer_status', 'status')
    search_fields = ('plate', 'vin', 'brand', 'model')
    list_filter = ('status', 'odometer_status', 'fuel_type', 'brand')
    # Hacemos que el campo de odómetro no se pueda editar manualmente aquí
    readonly_fields = ('current_odometer_km',)
