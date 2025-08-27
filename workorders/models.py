# workorders/models.py (Versión con Manual de Mantenimiento)
from django.db import models
from django.conf import settings
from fleet.models import Vehicle
from inventory.models import Part

# --- NUEVO: El Manual de Mantenimiento ---
class MaintenanceManual(models.Model):
    name = models.CharField("Nombre del Manual", max_length=150, unique=True, help_text="Ej: Plan Diesel Liviano, Plan Gasolina Avanzado")
    fuel_type = models.CharField("Aplica a Tipo de Combustible", max_length=20, choices=Vehicle.FuelType.choices, null=True, blank=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Manual de Mantenimiento"
        verbose_name_plural = "Manuales de Mantenimiento"

class ManualTask(models.Model):
    manual = models.ForeignKey(MaintenanceManual, on_delete=models.CASCADE, related_name="tasks")
    km_interval = models.PositiveIntegerField("Hito de Kilometraje (km)", help_text="Ej: 10000, 20000, 40000")
    description = models.CharField("Descripción de la Tarea", max_length=255)
    
    def __str__(self):
        return f"A los {self.km_interval} km: {self.description}"
    class Meta:
        verbose_name = "Tarea de Manual"
        verbose_name_plural = "Tareas de Manual"
        ordering = ['km_interval']

# --- MODIFICADO: MaintenancePlan ahora usa un Manual ---
class MaintenancePlan(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="plans", verbose_name="Vehículo")
    manual = models.ForeignKey(MaintenanceManual, on_delete=models.PROTECT, verbose_name="Manual Aplicado", null=True, blank=True)
    
    last_service_km = models.PositiveIntegerField("Km del Último Preventivo", default=0, help_text="Se actualiza al cerrar OT Preventiva")
    last_service_date = models.DateField("Fecha del Último Preventivo", null=True, blank=True, help_text="Se actualiza automáticamente")
    is_active = models.BooleanField("Activo", default=False, help_text="Se activa automáticamente al cerrar la primera OT Preventiva")

    def __str__(self):
        return f"Plan para {self.vehicle.plate} (basado en {self.manual.name if self.manual else 'N/A'})"
    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"

# (El resto de los modelos se mantienen igual, pero los incluyo para que el archivo esté completo)
class MaintenanceCategory(models.Model):
    name = models.CharField("Nombre de la Categoría", max_length=100, unique=True); description = models.TextField("Descripción", blank=True)
    def __str__(self): return self.name
    class Meta: verbose_name="Categoría de Mantenimiento"; verbose_name_plural="Categorías de Mantenimiento"

class MaintenanceSubcategory(models.Model):
    category = models.ForeignKey(MaintenanceCategory, on_delete=models.CASCADE, related_name="subcategories", verbose_name="Categoría Principal"); name = models.CharField("Nombre de la Subcategoría", max_length=100); description = models.TextField("Descripción", blank=True)
    def __str__(self): return f"{self.category.name} -> {self.name}"
    class Meta: verbose_name="Subcategoría de Mantenimiento"; verbose_name_plural="Subcategorías de Mantenimiento"; unique_together = ('category', 'name')

class WorkOrder(models.Model):
    class OrderType(models.TextChoices): PREVENTIVE = 'PREVENTIVE', 'Preventivo'; CORRECTIVE = 'CORRECTIVE', 'Correctivo'
    class OrderStatus(models.TextChoices): SCHEDULED='SCHEDULED','Programada'; IN_RECEPTION='IN_RECEPTION','En Recepción'; IN_SERVICE='IN_SERVICE','En Servicio'; WAITING_PART='WAITING_PART','Espera Repuesto'; PENDING_APPROVAL='PENDING_APPROVAL','Pendiente Aprobación'; STOPPED_BY_CLIENT='STOPPED_BY_CLIENT','Detenida Cliente'; IN_ROAD_TEST='IN_ROAD_TEST','Prueba de Ruta'; COMPLETED='COMPLETED','Completada'; VERIFIED='VERIFIED','Verificada'; CANCELLED='CANCELLED','Cancelada'
    class Priority(models.TextChoices): LOW='LOW','Baja'; MEDIUM='MEDIUM','Media'; HIGH='HIGH','Alta'; URGENT='URGENT','Urgente'
    order_type = models.CharField("Tipo de OT", max_length=20, choices=OrderType.choices, default=OrderType.CORRECTIVE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, verbose_name="Vehículo")
    status = models.CharField("Estado", max_length=20, choices=OrderStatus.choices, default=OrderStatus.SCHEDULED)
    priority = models.CharField("Prioridad", max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_ots", verbose_name="Técnico Asignado")
    description = models.TextField("Descripción del Problema/Trabajo Principal")
    scheduled_start = models.DateTimeField("Inicio Programado", null=True, blank=True)
    scheduled_end = models.DateTimeField("Fin Programado (Estimado)", null=True, blank=True)
    check_in_at = models.DateTimeField("Ingreso Real", null=True, blank=True)
    check_out_at = models.DateTimeField("Salida Real", null=True, blank=True)
    # --- NUEVO: Kilometraje al momento de la OT ---
    odometer_at_service = models.PositiveIntegerField("Kilometraje al Ingresar", null=True, blank=True, help_text="KM del vehículo al momento de esta OT")
    labor_cost_internal = models.DecimalField("Costo MO Interna", max_digits=10, decimal_places=2, default=0.0)
    labor_cost_external = models.DecimalField("Costo MO Terceros", max_digits=10, decimal_places=2, default=0.0)
    parts_cost = models.DecimalField("Costo Repuestos", max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField("Fecha de Creación", auto_now_add=True)
    def __str__(self): return f"OT-{self.id} ({self.get_order_type_display()}) para {self.vehicle.plate}"
    class Meta: verbose_name = "Orden de Trabajo"; verbose_name_plural = "Órdenes de Trabajo"; ordering = ['-created_at']

class WorkOrderTask(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="Orden de Trabajo")
    category = models.ForeignKey(MaintenanceCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría")
    subcategory = models.ForeignKey(MaintenanceSubcategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subcategoría")
    description = models.CharField("Descripción del Trabajo", max_length=255, blank=True)
    hours_spent = models.DecimalField("Horas Invertidas", max_digits=5, decimal_places=2, default=0.0)
    is_external = models.BooleanField("Realizado por Tercero", default=False)
    labor_rate = models.DecimalField("Tarifa o Costo Fijo (Tercero)", max_digits=10, decimal_places=2, null=True, blank=True)
    evidence_urls = models.JSONField("URLs de Evidencias", default=list, blank=True)
    def __str__(self): return str(self.subcategory) if self.subcategory else self.description
    class Meta: verbose_name = "Trabajo Adicional de OT"; verbose_name_plural = "Trabajos Adicionales de OT"

class WorkOrderPart(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="parts_used")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, verbose_name="Repuesto")
    quantity = models.DecimalField("Cantidad Usada", max_digits=10, decimal_places=2, default=1.0)
    cost_at_moment = models.DecimalField("Costo al Momento de Uso", max_digits=10, decimal_places=2)
    class Meta: unique_together = ('work_order', 'part'); verbose_name = "Repuesto Usado en OT"; verbose_name_plural = "Repuestos Usados en OT"
