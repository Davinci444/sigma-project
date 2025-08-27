# core/admin.py (Versión Corregida)
from django.contrib import admin
from .models import Alert, FuelFill, OdometerReading

# (La acción manual se queda igual)
def run_daily_jobs_action(modeladmin, request, queryset):
    from .management.commands import run_daily_jobs
    from django.contrib import messages
    try:
        command = run_daily_jobs.Command()
        command.handle()
        modeladmin.message_user(request, "Las tareas diarias se han ejecutado con éxito.", messages.SUCCESS)
    except Exception as e:
        modeladmin.message_user(request, f"Ocurrió un error: {e}", messages.ERROR)
run_daily_jobs_action.short_description = "Ejecutar Tareas Diarias (Preventivos/Stock)"


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'message', 'seen', 'created_at')
    list_filter = ('alert_type', 'severity', 'seen')
    actions = [run_daily_jobs_action]

# Registramos los nuevos modelos para que aparezcan en el admin
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