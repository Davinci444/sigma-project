# workorders/admin.py (Versión con Ciclo de Vida Preventivo Inteligente)
from django.contrib import admin, messages
from django.utils import timezone
from .models import (
    MaintenancePlan, 
    WorkOrder, 
    WorkOrderTask, 
    WorkOrderPart,
    MaintenanceCategory,
    MaintenanceSubcategory,
    MaintenanceManual,
    ManualTask
)

class MaintenanceSubcategoryInline(admin.TabularInline):
    model = MaintenanceSubcategory
    extra = 1

@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [MaintenanceSubcategoryInline]

class ManualTaskInline(admin.TabularInline):
    model = ManualTask
    extra = 1

@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ('name', 'fuel_type')
    inlines = [ManualTaskInline]

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1
    fields = ('category', 'subcategory', 'description', 'hours_spent', 'is_external', 'labor_rate')

class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'manual', 'is_active', 'last_service_km', 'last_service_date')
    list_filter = ('is_active', 'manual')
    readonly_fields = ('is_active', 'last_service_km', 'last_service_date')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_type', 'vehicle', 'status', 'priority', 'scheduled_start')
    search_fields = ('id', 'vehicle__plate', 'description')
    list_filter = ('status', 'priority', 'order_type')
    inlines = [WorkOrderTaskInline, WorkOrderPartInline]

    fieldsets = (
        ('Información Principal', {
            'fields': ('order_type', 'vehicle', 'status', 'priority', 'assigned_technician', 'odometer_at_service')
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

    # --- NUEVA LÓGICA: Activación y Reinicio de Planes ---
    def save_model(self, request, obj, form, change):
        # Esta función se ejecuta cada vez que se guarda una OT en el admin.
        super().save_model(request, obj, form, change) # Primero, guardamos la OT.

        # Verificamos si la OT es PREVENTIVA y se está CERRANDO (VERIFIED).
        if obj.order_type == WorkOrder.OrderType.PREVENTIVE and obj.status == WorkOrder.OrderStatus.VERIFIED:
            plan = MaintenancePlan.objects.filter(vehicle=obj.vehicle).first()
            
            if plan and obj.odometer_at_service:
                # Si el plan no estaba activo, lo activamos (es el "Kilómetro Cero").
                if not plan.is_active:
                    plan.is_active = True
                
                # Reiniciamos el contador con los datos de esta OT.
                plan.last_service_km = obj.odometer_at_service
                plan.last_service_date = obj.check_out_at.date() if obj.check_out_at else timezone.now().date()
                plan.save()
                
                messages.success(request, f"Plan de mantenimiento para {obj.vehicle.plate} ha sido activado/actualizado.")

    # --- LÓGICA CORREGIDA: Banner de Advertencia ---
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.vehicle:
            vehicle = obj.vehicle
            plan = MaintenancePlan.objects.filter(vehicle=vehicle, is_active=True).first()

            if plan and plan.manual and vehicle.odometer_status == 'VALID':
                # Buscamos la próxima tarea que le toca según el manual
                km_since_last_service = vehicle.current_odometer_km - plan.last_service_km
                
                next_task = plan.manual.tasks.filter(km_interval__gt=km_since_last_service).order_by('km_interval').first()
                
                if not next_task: # Si ya pasó la última tarea del manual
                    next_task = plan.manual.tasks.order_by('-km_interval').first()

                if next_task:
                    # El próximo servicio es el KM del último servicio + el hito de la próxima tarea
                    next_due_km = plan.last_service_km + next_task.km_interval
                    
                    if vehicle.current_odometer_km >= next_due_km:
                        mensaje = (f"¡Mantenimiento Preventivo VENCIDO! "
                                   f"Próximo servicio ({next_task.description}) era a los {next_due_km} km.")
                        messages.warning(request, f"ATENCIÓN: {mensaje}")

        return super().render_change_form(request, context, add, change, form_url, obj)
