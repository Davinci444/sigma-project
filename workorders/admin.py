# workorders/admin.py (Versión Final con todas las mejoras)
from django.contrib import admin
from .models import (
    MaintenancePlan, 
    WorkOrder, 
    WorkOrderTask, 
    WorkOrderPart,
    MaintenanceCategory,
    MaintenanceSubcategory
)

class MaintenanceSubcategoryInline(admin.TabularInline):
    model = MaintenanceSubcategory
    extra = 1

@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [MaintenanceSubcategoryInline]

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1
    fields = ('category', 'subcategory', 'description', 'hours_spent', 'is_external', 'labor_rate')

class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'plan_type', 'threshold_km', 'is_active')
    list_filter = ('plan_type', 'is_active')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    # --- AÑADIMOS 'order_type' A LA VISTA ---
    list_display = ('id', 'order_type', 'vehicle', 'status', 'priority', 'scheduled_start')
    search_fields = ('id', 'vehicle__plate', 'description')
    list_filter = ('status', 'priority', 'order_type')
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

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # ... (código del banner sin cambios)
        from django.contrib import messages
        from django.utils import timezone
        from datetime import timedelta
        if obj and obj.vehicle:
            vehicle = obj.vehicle
            plan = MaintenancePlan.objects.filter(vehicle=vehicle, is_active=True).first()
            if plan:
                vencido = False
                mensaje = ""
                if vehicle.odometer_status == 'VALID':
                    next_due_km = plan.last_service_km + plan.threshold_km
                    if vehicle.current_odometer_km >= next_due_km:
                        vencido = True
                        mensaje = f"¡Mantenimiento Preventivo VENCIDO por Kilometraje! Próximo servicio era a los {next_due_km} km."
                else:
                    if plan.last_service_date:
                        next_due_date = plan.last_service_date + timedelta(days=plan.threshold_days)
                        if timezone.now().date() >= next_due_date:
                            vencido = True
                            mensaje = f"¡Mantenimiento Preventivo VENCIDO por Tiempo! (Odómetro inválido). Próximo servicio era el {next_due_date}."
                if vencido:
                    messages.warning(request, f"ATENCIÓN: {mensaje} Se recomienda crear una OT Preventiva.")
        return super().render_change_form(request, context, add, change, form_url, obj)
