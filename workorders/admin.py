# workorders/admin.py (Versión con interfaz mejorada)
from django.contrib import admin
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

    # --- NUEVO: Organizamos el formulario en secciones ---
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
            'classes': ('collapse',), # Esta sección aparecerá colapsada por defecto
        }),
    )

    # Hacemos que los campos de costos sean de solo lectura, ya que se calculan solos
    readonly_fields = ('labor_cost_internal', 'labor_cost_external', 'parts_cost')

