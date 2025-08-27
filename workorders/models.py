# workorders/models.py

from django.db import models
from django.conf import settings
from fleet.models import Vehicle

class MaintenancePlan(models.Model):
    class PlanType(models.TextChoices):
        KILOMETERS = 'KM', 'Kilometraje'
        TIME = 'TIME', 'Tiempo (días)'
        ENGINE_HOURS = 'HOURS', 'Horas de Motor'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="plans", verbose_name="Vehículo")
    plan_type = models.CharField("Tipo de Plan", max_length=10, choices=PlanType.choices)
    threshold_value = models.PositiveIntegerField("Valor Umbral", help_text="Kilómetros, Días u Horas de motor para la próxima activación")
    last_execution_value = models.PositiveIntegerField("Valor en Última Ejecución", default=0, help_text="Odómetro, fecha (en días) u horas en el último mantenimiento")
    is_active = models.BooleanField("Activo", default=True)
    description = models.CharField("Descripción del Plan", max_length=255)

    def __str__(self):
        return f"Plan {self.get_plan_type_display()} para {self.vehicle.plate} cada {self.threshold_value}"

    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"


class WorkOrder(models.Model):
    class OrderStatus(models.TextChoices):
        OPEN = 'OPEN', 'Abierta'
        IN_PROGRESS = 'IN_PROGRESS', 'En Progreso'
        WAITING_PART = 'WAITING_PART', 'En Espera de Repuesto'
        COMPLETED = 'COMPLETED', 'Completada'
        VERIFIED = 'VERIFIED', 'Verificada (Cerrada)'
        CANCELLED = 'CANCELLED', 'Cancelada'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        URGENT = 'URGENT', 'Urgente'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, verbose_name="Vehículo")
    status = models.CharField("Estado", max_length=20, choices=OrderStatus.choices, default=OrderStatus.OPEN)
    priority = models.CharField("Prioridad", max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Asignaciones
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_ots", verbose_name="Técnico Asignado")
    
    # Descripción y fechas
    description = models.TextField("Descripción del Problema/Trabajo")
    created_at = models.DateTimeField("Fecha de Apertura", auto_now_add=True)
    completed_at = models.DateTimeField("Fecha de Cierre", null=True, blank=True)
    
    # Costos
    labor_cost = models.DecimalField("Costo Mano de Obra", max_digits=10, decimal_places=2, default=0.0)
    parts_cost = models.DecimalField("Costo Repuestos", max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"OT-{self.id} para {self.vehicle.plate} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = ['-created_at']


class WorkOrderTask(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="Orden de Trabajo")
    title = models.CharField("Título de la Tarea", max_length=255)
    hours_spent = models.DecimalField("Horas Invertidas", max_digits=5, decimal_places=2, default=0.0)
    # Aquí guardaríamos la URL a un archivo subido (ej. una foto)
    evidence_url = models.URLField("URL de Evidencia", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Tarea de OT"
        verbose_name_plural = "Tareas de OT"