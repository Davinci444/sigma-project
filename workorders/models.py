# workorders/models.py

from django.db import models
from django.conf import settings
from fleet.models import Vehicle
from inventory.models import Part

# --- NUEVOS MODELOS PARA CATEGORIZACIÓN ---
class MaintenanceCategory(models.Model):
    name = models.CharField("Nombre de la Categoría", max_length=100, unique=True)
    description = models.TextField("Descripción", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoría de Mantenimiento"
        verbose_name_plural = "Categorías de Mantenimiento"

class MaintenanceSubcategory(models.Model):
    category = models.ForeignKey(MaintenanceCategory, on_delete=models.CASCADE, related_name="subcategories", verbose_name="Categoría Principal")
    name = models.CharField("Nombre de la Subcategoría", max_length=100)
    description = models.TextField("Descripción", blank=True)

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

    class Meta:
        verbose_name = "Subcategoría de Mantenimiento"
        verbose_name_plural = "Subcategorías de Mantenimiento"
        unique_together = ('category', 'name')

# (El modelo MaintenancePlan se queda igual por ahora)
class MaintenancePlan(models.Model):
    class PlanType(models.TextChoices):
        KM_TIME = 'KM_TIME', 'Kilometraje (con respaldo por tiempo)'
        TIME = 'TIME', 'Solo por Tiempo (días)'
        ENGINE_HOURS = 'HOURS', 'Solo por Horas de Motor'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="plans", verbose_name="Vehículo")
    plan_type = models.CharField("Tipo de Plan", max_length=10, choices=PlanType.choices, default=PlanType.KM_TIME)
    threshold_km = models.PositiveIntegerField("Umbral de Kilometraje (km)", default=10000) # Estandarizamos a 10,000 km
    threshold_days = models.PositiveIntegerField("Umbral de Tiempo (días)", default=180)
    grace_km = models.PositiveIntegerField("Kilometraje de Gracia", default=500)
    last_service_km = models.PositiveIntegerField("Km en Último Servicio", default=0, help_text="Se actualiza automáticamente al cerrar una OT Preventiva")
    last_service_date = models.DateField("Fecha del Último Servicio", null=True, blank=True, help_text="Se actualiza automáticamente")
    is_active = models.BooleanField("Activo", default=True, help_text="El plan está 'dormido' hasta que se cierra la primera OT Preventiva")
    description = models.CharField("Descripción del Plan", max_length=255)

    def __str__(self):
        return f"Plan {self.get_plan_type_display()} para {self.vehicle.plate}"

    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"

# (El modelo WorkOrder se queda igual)
class WorkOrder(models.Model):
    class OrderType(models.TextChoices):
        PREVENTIVE = 'PREVENTIVE', 'Preventivo'
        CORRECTIVE = 'CORRECTIVE', 'Correctivo'
    # ... (resto de los campos de WorkOrder sin cambios)
    order_type = models.CharField("Tipo de OT", max_length=20, choices=OrderType.choices, default=OrderType.CORRECTIVE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, verbose_name="Vehículo")
    status = models.CharField("Estado", max_length=20, choices=models.TextChoices('OrderStatus', 'SCHEDULED IN_RECEPTION IN_SERVICE WAITING_PART PENDING_APPROVAL STOPPED_BY_CLIENT IN_ROAD_TEST COMPLETED VERIFIED CANCELLED').choices, default='SCHEDULED')
    priority = models.CharField("Prioridad", max_length=20, choices=models.TextChoices('Priority', 'LOW MEDIUM HIGH URGENT').choices, default='MEDIUM')
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_ots", verbose_name="Técnico Asignado")
    description = models.TextField("Descripción del Problema/Trabajo Principal")
    scheduled_start = models.DateTimeField("Inicio Programado", null=True, blank=True)
    scheduled_end = models.DateTimeField("Fin Programado (Estimado)", null=True, blank=True)
    check_in_at = models.DateTimeField("Fecha y Hora de Ingreso Real", null=True, blank=True)
    check_out_at = models.DateTimeField("Fecha y Hora de Salida Real", null=True, blank=True)
    labor_cost_internal = models.DecimalField("Costo MO Interna", max_digits=10, decimal_places=2, default=0.0)
    labor_cost_external = models.DecimalField("Costo MO Terceros", max_digits=10, decimal_places=2, default=0.0)
    parts_cost = models.DecimalField("Costo Repuestos", max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField("Fecha de Creación", auto_now_add=True)

    def __str__(self):
        return f"OT-{self.id} ({self.get_order_type_display()}) para {self.vehicle.plate}"

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = ['-created_at']


# --- MODIFICACIÓN IMPORTANTE EN WorkOrderTask ---
class WorkOrderTask(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="Orden de Trabajo")
    
    # Nuevos campos para categorización
    category = models.ForeignKey(MaintenanceCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría")
    subcategory = models.ForeignKey(MaintenanceSubcategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subcategoría")
    
    description = models.CharField("Descripción del Trabajo (si no aplica subcategoría)", max_length=255, blank=True)
    hours_spent = models.DecimalField("Horas Invertidas", max_digits=5, decimal_places=2, default=0.0)
    
    is_external = models.BooleanField("Realizado por Tercero", default=False)
    labor_rate = models.DecimalField("Tarifa o Costo Fijo (Tercero)", max_digits=10, decimal_places=2, null=True, blank=True)
    
    evidence_urls = models.JSONField("URLs de Evidencias", default=list, blank=True)

    def __str__(self):
        if self.subcategory:
            return str(self.subcategory)
        return self.description

    class Meta:
        verbose_name = "Trabajo Adicional de OT"
        verbose_name_plural = "Trabajos Adicionales de OT"

# (El modelo WorkOrderPart se queda igual)
class WorkOrderPart(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="parts_used")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, verbose_name="Repuesto")
    quantity = models.PositiveIntegerField("Cantidad Usada", default=1)
    cost_at_moment = models.DecimalField("Costo al Momento de Uso", max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('work_order', 'part')
        verbose_name = "Repuesto Usado en OT"
        verbose_name_plural = "Repuestos Usados en OT"

