# workorders/admin.py
from django.contrib import admin
from .models import MaintenancePlan, WorkOrder, WorkOrderTask

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'plan_type', 'threshold_value', 'is_active')
    list_filter = ('plan_type', 'is_active')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'status', 'priority', 'assigned_technician', 'created_at', 'completed_at')
    search_fields = ('id', 'vehicle__plate', 'description')
    list_filter = ('status', 'priority', 'assigned_technician')

admin.site.register(WorkOrderTask) # Registro simple para las tareas