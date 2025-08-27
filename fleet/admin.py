# fleet/admin.py (Versión con Filtro Operativo Corregido)
from django.contrib import admin
from .models import Vehicle, VehicleZoneHistory

# --- NUEVO: Filtro por Estado Operativo del Vehículo ---
class VehicleOperationalStatusFilter(admin.SimpleListFilter):
    title = 'Estado Operativo'
    parameter_name = 'operational_status'

    def lookups(self, request, model_admin):
        return (
            ('in_repair', 'En Taller (Reparación)'),
        )

    def queryset(self, request, queryset):
        # Filtramos directamente por el estado del vehículo
        if self.value() == 'in_repair':
            return queryset.filter(status=Vehicle.VehicleStatus.IN_REPAIR)
        return queryset

class VehicleZoneHistoryInline(admin.TabularInline):
    model = VehicleZoneHistory
    extra = 0
    readonly_fields = ('start_date', 'end_date')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'current_zone', 'status', 'current_odometer_km')
    search_fields = ('plate', 'vin', 'brand', 'model')
    # --- AÑADIMOS EL NUEVO FILTRO ---
    list_filter = (VehicleOperationalStatusFilter, 'status', 'current_zone', 'fuel_type')
    readonly_fields = ('current_odometer_km',)
    
    fieldsets = (
        (None, {'fields': ('plate', 'vin', 'brand', 'model', 'year', 'vehicle_type', 'fuel_type', 'status')}),
        ('Operación y Estado', {'fields': ('current_zone', 'current_odometer_km', 'odometer_status')}),
        ('Documentación', {'fields': ('soat_due_date', 'rtm_due_date')}),
    )
    inlines = [VehicleZoneHistoryInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            try:
                user_zone = request.user.profile.zone
                if user_zone:
                    return qs.filter(current_zone=user_zone)
            except AttributeError:
                return qs.none()
        return qs