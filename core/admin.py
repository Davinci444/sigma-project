# core/admin.py
from django.contrib import admin
from .models import Alert, FuelFill, OdometerReading, Zone

# --- HEMOS ELIMINADO LA ACCIÓN DE AQUÍ ---


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("alert_type", "severity", "message", "seen", "created_at")
    list_filter = ("alert_type", "severity", "seen")
    # La lista de 'actions' ahora está vacía


@admin.register(FuelFill)
class FuelFillAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "fill_date", "odometer_km", "gallons")
    list_filter = ("fill_date",)
    search_fields = ("vehicle__plate",)


@admin.register(OdometerReading)
class OdometerReadingAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "reading_date", "reading_km", "source", "is_anomaly")
    list_filter = ("source", "is_anomaly", "reading_date")
    search_fields = ("vehicle__plate",)
