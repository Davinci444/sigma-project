# fleet/admin.py (Versión con Permisos por Zona)
from django.contrib import admin
from .models import Vehicle, VehicleZoneHistory

class VehicleZoneHistoryInline(admin.TabularInline):
    model = VehicleZoneHistory
    extra = 0
    readonly_fields = ('start_date', 'end_date')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'current_zone', 'current_odometer_km', 'status')
    search_fields = ('plate', 'vin', 'brand', 'model')
    list_filter = ('status', 'current_zone', 'fuel_type')
    readonly_fields = ('current_odometer_km',)
    
    fieldsets = (
        (None, {'fields': ('plate', 'vin', 'brand', 'model', 'year', 'vehicle_type', 'fuel_type', 'status')}),
        ('Operación y Estado', {'fields': ('current_zone', 'current_odometer_km', 'odometer_status')}),
        ('Documentación', {'fields': ('soat_due_date', 'rtm_due_date')}),
    )
    inlines = [VehicleZoneHistoryInline]

    # --- NUEVA LÓGICA DE SEGURIDAD ---
    def get_queryset(self, request):
        # Obtenemos la lista normal de vehículos
        qs = super().get_queryset(request)
        
        # Si el usuario no es un superadministrador, filtramos por su zona
        if not request.user.is_superuser:
            try:
                # Buscamos la zona asignada al perfil del usuario
                user_zone = request.user.profile.zone
                if user_zone:
                    return qs.filter(current_zone=user_zone)
            except AttributeError:
                # Si el usuario no tiene perfil o zona, no ve ningún vehículo
                return qs.none()
        
        # El superadministrador ve todos los vehículos
        return qs
