# workorders/admin.py (Versión con interfaz y advertencias inteligentes)
from django.contrib import admin, messages
from django.utils import timezone
from datetime import timedelta
from .models import MaintenancePlan, WorkOrder, WorkOrderTask, WorkOrderPart

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1

class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'plan_type', 'threshold_km', 'threshold_days', 'is_active')
    list_filter = ('plan_type', 'is_active')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_type', 'vehicle', 'status', 'priority', 'assigned_technician', 'scheduled_start')
    search_fields = ('id', 'vehicle__plate', 'description')
    list_filter = ('status', 'priority', 'order_type', 'assigned_technician')
    inlines = [WorkOrderTaskInline, WorkOrderPartInline]

    fieldsets = (
        ('Información Principal', {
            'fields': ('order_type', 'vehicle', 'status', 'priority', 'assigned_technician')
        }),
        ('Descripción del Trabajo', {
            'fields': ('description',)
        }),
        ('Programación y Tiempos', {
            'fields': ('scheduled_start', 'scheduled_end', 'check_in_at', 'check_out_at')
        }),
        ('Costos (Calculados)', {
            'fields': ('labor_cost_internal', 'labor_cost_external', 'parts_cost'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('labor_cost_internal', 'labor_cost_external', 'parts_cost')

    # --- NUEVO: Lógica para el banner de advertencia ---
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # Esta función se ejecuta cada vez que se abre el formulario de una OT.
        if obj and obj.vehicle: # Si estamos editando una OT que ya tiene un vehículo asignado
            vehicle = obj.vehicle
            # Buscamos el plan de mantenimiento activo para este vehículo
            plan = MaintenancePlan.objects.filter(vehicle=vehicle, is_active=True).first()

            if plan:
                vencido = False
                mensaje = ""
                # Lógica de Vencimiento por Kilometraje
                if vehicle.odometer_status == 'VALID':
                    next_due_km = plan.last_service_km + plan.threshold_km
                    if vehicle.current_odometer_km >= next_due_km:
                        vencido = True
                        mensaje = f"¡Mantenimiento Preventivo VENCIDO por Kilometraje! Próximo servicio era a los {next_due_km} km."
                
                # Lógica de Vencimiento por Tiempo (si el odómetro es inválido)
                else:
                    if plan.last_service_date:
                        next_due_date = plan.last_service_date + timedelta(days=plan.threshold_days)
                        if timezone.now().date() >= next_due_date:
                            vencido = True
                            mensaje = f"¡Mantenimiento Preventivo VENCIDO por Tiempo! (Odómetro inválido). Próximo servicio era el {next_due_date}."
                
                if vencido:
                    # Si está vencido, mostramos un mensaje de advertencia grande y claro.
                    messages.warning(request, f"ATENCIÓN: {mensaje} Se recomienda crear una OT Preventiva.")

        return super().render_change_form(request, context, add, change, form_url, obj)
