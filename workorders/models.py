# workorders/models.py

from django.db import models
from django.conf import settings
from fleet.models import Vehicle
from inventory.models import Part # Importamos el modelo Part

class MaintenancePlan(models.Model):
    # (Este modelo se queda casi igual, solo ajustamos los textos de ayuda)
    class PlanType(models.TextChoices):
        KM_TIME = 'KM_TIME', 'Kilometraje (con respaldo por tiempo)'
        TIME = 'TIME', 'Solo por Tiempo (días)'
        ENGINE_HOURS = 'HOURS', 'Solo por Horas de Motor'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="plans", verbose_name="Vehículo")
    plan_type = models.CharField("Tipo de Plan", max_length=10, choices=PlanType.choices, default=PlanType.KM_TIME)
    
    # Umbrales
    threshold_km = models.PositiveIntegerField("Umbral de Kilometraje (km)", default=5000)
    threshold_days = models.PositiveIntegerField("Umbral de Tiempo (días)", default=180)
    grace_km = models.PositiveIntegerField("Kilometraje de Gracia", default=500, help_text="Km extra antes de considerarse vencido")

    # Estado calculado
    last_service_km = models.PositiveIntegerField("Km en Último Servicio", default=0)
    last_service_date = models.DateField("Fecha del Último Servicio", null=True, blank=True)
    
    is_active = models.BooleanField("Activo", default=True)
    description = models.CharField("Descripción del Plan", max_length=255)

    def __str__(self):
        return f"Plan {self.get_plan_type_display()} para {self.vehicle.plate}"

    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"


class WorkOrder(models.Model):
    class OrderType(models.TextChoices):
        PREVENTIVE = 'PREVENTIVE', 'Preventivo'
        CORRECTIVE = 'CORRECTIVE', 'Correctivo'

    class OrderStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Programada'
        IN_RECEPTION = 'IN_RECEPTION', 'En Recepción'
        IN_SERVICE = 'IN_SERVICE', 'En Servicio'
        WAITING_PART = 'WAITING_PART', 'En Espera de Repuesto'
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pendiente de Aprobación'
        STOPPED_BY_CLIENT = 'STOPPED_BY_CLIENT', 'Detenida por Cliente'
        IN_ROAD_TEST = 'IN_ROAD_TEST', 'En Prueba de Ruta'
        COMPLETED = 'COMPLETED', 'Completada (Taller)'
        VERIFIED = 'VERIFIED', 'Verificada (Cerrada)'
        CANCELLED = 'CANCELLED', 'Cancelada'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        URGENT = 'URGENT', 'Urgente'
    
    # --- NUEVOS CAMPOS ---
    order_type = models.CharField("Tipo de OT", max_length=20, choices=OrderType.choices, default=OrderType.CORRECTIVE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, verbose_name="Vehículo")
    status = models.CharField("Estado", max_length=20, choices=OrderStatus.choices, default=OrderStatus.SCHEDULED)
    priority = models.CharField("Prioridad", max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_ots", verbose_name="Técnico Asignado")
    
    description = models.TextField("Descripción del Problema/Trabajo Principal")
    
    # --- NUEVOS CAMPOS DE PROGRAMACIÓN ---
    scheduled_start = models.DateTimeField("Inicio Programado", null=True, blank=True)
    scheduled_end = models.DateTimeField("Fin Programado (Estimado)", null=True, blank=True)
    check_in_at = models.DateTimeField("Fecha y Hora de Ingreso Real", null=True, blank=True)
    check_out_at = models.DateTimeField("Fecha y Hora de Salida Real", null=True, blank=True)

    # Costos (ahora se calculan desde las tareas y repuestos)
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


class WorkOrderTask(models.Model):
    # --- CAMPOS AMPLIADOS ---
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="Orden de Trabajo")
    # --- CORRECCIÓN AQUÍ ---
    description = models.CharField("Descripción del Trabajo Adicional", max_length=255, default="")
    hours_spent = models.DecimalField("Horas Invertidas", max_digits=5, decimal_places=2, default=0.0)
    
    # Costeo por terceros
    is_external = models.BooleanField("Realizado por Tercero", default=False)
    labor_rate = models.DecimalField("Tarifa por Hora o Costo Fijo (Tercero)", max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Evidencias (ahora puede ser una lista de URLs)
    evidence_urls = models.JSONField("URLs de Evidencias", default=list, blank=True)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Trabajo Adicional de OT"
        verbose_name_plural = "Trabajos Adicionales de OT"


class WorkOrderPart(models.Model):
    """Modelo para vincular repuestos a una OT."""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="parts_used")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, verbose_name="Repuesto")
    quantity = models.PositiveIntegerField("Cantidad Usada", default=1)
    cost_at_moment = models.DecimalField("Costo al Momento de Uso", max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('work_order', 'part') # No se puede añadir el mismo repuesto dos veces a la misma OT
        verbose_name = "Repuesto Usado en OT"
        verbose_name_plural = "Repuestos Usados en OT"