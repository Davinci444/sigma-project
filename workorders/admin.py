# workorders/admin.py (Versión con Biblioteca de Fallas)
from django.contrib import admin
from .models import (
    MaintenancePlan, 
    WorkOrder, 
    WorkOrderTask, 
    WorkOrderPart,
    MaintenanceCategory,      # <-- Importamos los nuevos modelos
    MaintenanceSubcategory
)

# --- NUEVO: Admin para Subcategorías anidado dentro de Categorías ---
class MaintenanceSubcategoryInline(admin.TabularInline):
    model = MaintenanceSubcategory
    extra = 1

@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [MaintenanceSubcategoryInline] # <-- Mostramos las subcategorías aquí


# --- Mejoramos la interfaz para añadir Tareas ---
class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1 # Empezar con un campo para añadir una nueva tarea
    # Hacemos que los campos se organicen mejor
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

    # (La lógica del banner de advertencia se queda igual)
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # ... (código del banner sin cambios)
        return super().render_change_form(request, context, add, change, form_url, obj)

# No registramos MaintenanceSubcategory por separado porque ya está dentro de Category
