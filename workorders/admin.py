# workorders/admin.py (Versión Corregida)
from django.contrib import admin
from .models import MaintenancePlan, WorkOrder, WorkOrderTask, WorkOrderPart

# Para mostrar las tareas y repuestos DENTRO de la orden de trabajo
class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1 # Muestra un campo vacío para añadir una nueva tarea

class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1 # Muestra un campo vacío para añadir un nuevo repuesto

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    # Usamos los nuevos campos 'threshold_km' y 'threshold_days'
    list_display = ('vehicle', 'plan_type', 'threshold_km', 'threshold_days', 'is_active')
    list_filter = ('plan_type', 'is_active')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    # Quitamos 'completed_at' y añadimos 'order_type'
    list_display = ('id', 'order_type', 'vehicle', 'status', 'priority', 'assigned_technician', 'created_at')
    search_fields = ('id', 'vehicle__plate', 'description')
    list_filter = ('status', 'priority', 'order_type', 'assigned_technician')
    inlines = [WorkOrderTaskInline, WorkOrderPartInline] # Mostramos tareas y repuestos aquí

# No necesitamos registrar WorkOrderTask y WorkOrderPart aquí porque ya están como 'inlines'
