# fleet/admin.py
from django.contrib import admin
from .models import Vehicle, VehicleZoneHistory

# --- Mostramos el historial de zonas dentro del vehículo ---
class VehicleZoneHistoryInline(admin.TabularInline):
    model = VehicleZoneHistory
    extra = 0 # No mostrar campos vacíos por defecto
    readonly_fields = ('start_date', 'end_date') # El historial no se edita aquí

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'current_zone', 'current_odometer_km', 'status')
    search_fields = ('plate', 'vin', 'brand', 'model')
    list_filter = ('status', 'current_zone', 'fuel_type')
    readonly_fields = ('current_odometer_km',)
    
    # Añadimos la zona al formulario y el historial abajo
    fieldsets = (
        (None, {
            'fields': ('plate', 'vin', 'brand', 'model', 'year', 'vehicle_type', 'fuel_type', 'status')
        }),
        ('Operación y Estado', {
            'fields': ('current_zone', 'current_odometer_km', 'odometer_status')
        }),
        ('Documentación', {
            'fields': ('soat_due_date', 'rtm_due_date')
        }),
    )
    inlines = [VehicleZoneHistoryInline]
