# core/admin.py (con acción manual)
from django.contrib import admin, messages
from .models import Alert
from .management.commands import run_daily_jobs # Importamos nuestro comando

def run_daily_jobs_action(modeladmin, request, queryset):
    """
    Acción del admin que ejecuta nuestro comando de tareas diarias.
    """
    try:
        command = run_daily_jobs.Command()
        command.handle()
        modeladmin.message_user(request, "Las tareas diarias (revisión de preventivos, stock y vencimientos) se han ejecutado con éxito.", messages.SUCCESS)
    except Exception as e:
        modeladmin.message_user(request, f"Ocurrió un error al ejecutar las tareas: {e}", messages.ERROR)

run_daily_jobs_action.short_description = "Ejecutar Tareas Diarias (Preventivos/Stock)"


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'message', 'seen', 'created_at')
    list_filter = ('alert_type', 'severity', 'seen')
    # Añadimos la nueva acción a la lista de acciones disponibles en el modelo de Alertas.
    actions = [run_daily_jobs_action]