# core/admin.py
from django.contrib import admin
from .models import Alert, FuelFill, OdometerReading, Zone # Importamos Zone

# (La acción manual se queda igual)
def run_daily_jobs_action(modeladmin, request, queryset):
    from .management.commands import run_daily_jobs
    from django.contrib import messages
    try:
        command = run_daily_jobs.Command()
        # Simulamos que no hay archivo para solo recalcular planes
        command.handle(file_path=None) 
        modeladmin.message_user(request, "Las tareas diarias (revisión de preventivos, stock y vencimientos) se han ejecutado con éxito.", messages.SUCCESS)
    except Exception as e:
        modeladmin.message_user(request, f"Ocurrió un error al ejecutar las tareas: {e}", messages.ERROR)
run_daily_jobs_action.short_description = "Ejecutar Tareas Diarias (Preventivos/Stock)"


# --- NUEVO: Registramos el modelo de Zonas ---
@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'message', 'seen', 'created_at')
    list_filter = ('alert_type', 'severity', 'seen')
    actions = [run_daily_jobs_action]

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