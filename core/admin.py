# core/admin.py
from django.contrib import admin
from django.core.management import call_command # Importamos call_command
from django.contrib import messages
from .models import Alert, FuelFill, OdometerReading, Zone

# --- ACCIÓN ACTUALIZADA ---
def run_periodic_checks_action(modeladmin, request, queryset):
    """
    Acción del admin que ejecuta nuestro nuevo comando de revisiones periódicas.
    """
    try:
        call_command('run_periodic_checks') # Llamamos al nuevo comando
        modeladmin.message_user(request, "Las revisiones periódicas (documentos, planes, etc.) se han ejecutado con éxito.", messages.SUCCESS)
    except Exception as e:
        modeladmin.message_user(request, f"Ocurrió un error al ejecutar las revisiones: {e}", messages.ERROR)

run_periodic_checks_action.short_description = "Ejecutar Revisiones Periódicas (Docs/Planes)"

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'message', 'seen', 'created_at')
    list_filter = ('alert_type', 'severity', 'seen')
    # --- USAMOS LA NUEVA ACCIÓN ---
    actions = [run_periodic_checks_action]

@admin.register(FuelFill)
class FuelFillAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'fill_date', 'odometer_km', 'gallons')
    list_filter = ('fill_date',)
    search_fields = ('vehicle__plate',)

@admin.register(OdometerReading)
class OdometerReadingAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'reading_date', 'reading_km', 'source', 'is_anomaly')
    list_filter = ('source', 'is_anomaly', 'reading_date')
    search_fields = ('vehicle__plate',)