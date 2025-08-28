"""Models for managing maintenance plans and work orders."""

from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from fleet.models import Vehicle
from inventory.models import Part


class MaintenanceManual(models.Model):
    """Maintenance manual defining tasks for a fuel type."""

    name = models.CharField(
        "Nombre del Manual",
        max_length=150,
        unique=True,
        help_text="Ej: Plan Diesel Liviano, Plan Gasolina Avanzado",
    )
    fuel_type = models.CharField(
        "Aplica a Tipo de Combustible",
        max_length=20,
        choices=Vehicle.FuelType.choices,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        """Return manual name."""

        return self.name

    class Meta:
        verbose_name = "Manual de Mantenimiento"
        verbose_name_plural = "Manuales de Mantenimiento"


class ManualTask(models.Model):
    """Task defined within a maintenance manual."""

    manual = models.ForeignKey(
        MaintenanceManual, on_delete=models.CASCADE, related_name="tasks"
    )
    km_interval = models.PositiveIntegerField(
        "Hito de Kilometraje (km)", help_text="Ej: 10000, 20000, 40000"
    )
    description = models.CharField("Descripción de la Tarea", max_length=255)

    def __str__(self) -> str:
        """Return a descriptive string for the task."""

        return f"A los {self.km_interval} km: {self.description}"

    class Meta:
        verbose_name = "Tarea de Manual"
        verbose_name_plural = "Tareas de Manual"
        ordering = ["km_interval"]


class MaintenancePlan(models.Model):
    """Associates a vehicle with a maintenance manual."""

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="plans", verbose_name="Vehículo"
    )
    manual = models.ForeignKey(
        MaintenanceManual,
        on_delete=models.PROTECT,
        verbose_name="Manual Aplicado",
        null=True,
        blank=True,
    )
    last_service_km = models.PositiveIntegerField(
        "Km del Último Preventivo",
        default=0,
        help_text="Se actualiza al cerrar OT Preventiva",
    )
    last_service_date = models.DateField(
        "Fecha del Último Preventivo",
        null=True,
        blank=True,
        help_text="Se actualiza automáticamente",
    )
    is_active = models.BooleanField(
        "Activo",
        default=False,
        help_text="Se activa automáticamente al cerrar la primera OT Preventiva",
    )

    def __str__(self) -> str:
        """Return a description of the plan."""

        manual_name = self.manual.name if self.manual else "N/A"
        return f"Plan para {self.vehicle.plate} (basado en {manual_name})"

    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"


class MaintenanceCategory(models.Model):
    """High-level maintenance category."""

    name = models.CharField("Nombre de la Categoría", max_length=100, unique=True)
    description = models.TextField("Descripción", blank=True)

    def __str__(self) -> str:
        """Return category name."""

        return self.name

    class Meta:
        verbose_name = "Categoría de Mantenimiento"
        verbose_name_plural = "Categorías de Mantenimiento"


class MaintenanceSubcategory(models.Model):
    """Detailed maintenance subcategory."""

    category = models.ForeignKey(
        MaintenanceCategory,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name="Categoría Principal",
    )
    name = models.CharField("Nombre de la Subcategoría", max_length=100)
    description = models.TextField("Descripción", blank=True)

    def __str__(self) -> str:
        """Return formatted subcategory name."""

        return f"{self.category.name} -> {self.name}"

    class Meta:
        verbose_name = "Subcategoría de Mantenimiento"
        verbose_name_plural = "Subcategorías de Mantenimiento"
        unique_together = ("category", "name")


class WorkOrder(models.Model):
    """Represents a maintenance or repair work order."""

    class OrderType(models.TextChoices):
        PREVENTIVE = "PREVENTIVE", "Preventivo"
        CORRECTIVE = "CORRECTIVE", "Correctivo"

    class OrderStatus(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Programada"
        IN_RECEPTION = "IN_RECEPTION", "En Recepción"
        IN_SERVICE = "IN_SERVICE", "En Servicio"
        WAITING_PART = "WAITING_PART", "Espera Repuesto"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pendiente Aprobación"
        STOPPED_BY_CLIENT = "STOPPED_BY_CLIENT", "Detenida Cliente"
        IN_ROAD_TEST = "IN_ROAD_TEST", "Prueba de Ruta"
        COMPLETED = "COMPLETED", "Completada"
        VERIFIED = "VERIFIED", "Verificada"
        CANCELLED = "CANCELLED", "Cancelada"

    class Priority(models.TextChoices):
        LOW = "LOW", "Baja"
        MEDIUM = "MEDIUM", "Media"
        HIGH = "HIGH", "Alta"
        URGENT = "URGENT", "Urgente"

    order_type = models.CharField(
        "Tipo de OT", max_length=20, choices=OrderType.choices, default=OrderType.CORRECTIVE
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, verbose_name="Vehículo"
    )
    status = models.CharField(
        "Estado", max_length=20, choices=OrderStatus.choices, default=OrderStatus.SCHEDULED
    )
    priority = models.CharField(
        "Prioridad", max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_ots",
        verbose_name="Técnico Asignado",
    )
    description = models.TextField("Descripción del Problema/Trabajo Principal")
    scheduled_start = models.DateTimeField("Inicio Programado", null=True, blank=True)
    scheduled_end = models.DateTimeField(
        "Fin Programado (Estimado)", null=True, blank=True
    )
    check_in_at = models.DateTimeField("Ingreso Real", null=True, blank=True)
    check_out_at = models.DateTimeField("Salida Real", null=True, blank=True)
    odometer_at_service = models.PositiveIntegerField(
        "Kilometraje al Ingresar",
        null=True,
        blank=True,
        help_text="KM del vehículo al momento de esta OT",
    )
    labor_cost_internal = models.DecimalField(
        "Costo MO Interna", max_digits=10, decimal_places=2, default=0.0
    )
    labor_cost_external = models.DecimalField(
        "Costo MO Terceros", max_digits=10, decimal_places=2, default=0.0
    )
    parts_cost = models.DecimalField(
        "Costo Repuestos", max_digits=10, decimal_places=2, default=0.0
    )
    created_at = models.DateTimeField("Fecha de Creación", auto_now_add=True)

    def __str__(self) -> str:
        """Return readable identifier for the work order."""

        return f"OT-{self.id} ({self.get_order_type_display()}) para {self.vehicle.plate}"

    def recalculate_costs(self) -> None:
        """Recalculate labor and parts costs based on related items."""

        labor_costs = self.tasks.aggregate(
            internal=Sum("hours_spent", filter=models.Q(is_external=False)),
            external=Sum("labor_rate", filter=models.Q(is_external=True)),
        )
        internal_rate = 50000  # TODO: make configurable
        self.labor_cost_internal = (labor_costs["internal"] or 0) * internal_rate
        self.labor_cost_external = labor_costs["external"] or 0

        parts_total = self.parts_used.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("cost_at_moment"),
                    output_field=DecimalField(),
                )
            )
        )["total"]
        self.parts_cost = parts_total or 0

        self.save(
            update_fields=["labor_cost_internal", "labor_cost_external", "parts_cost"]
        )

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = ["-created_at"]


class WorkOrderTask(models.Model):
    """Individual task associated with a work order."""

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="Orden de Trabajo"
    )
    category = models.ForeignKey(
        MaintenanceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoría",
    )
    subcategory = models.ForeignKey(
        MaintenanceSubcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Subcategoría",
    )
    description = models.CharField(
        "Descripción del Trabajo", max_length=255, blank=True
    )
    hours_spent = models.DecimalField(
        "Horas Invertidas", max_digits=5, decimal_places=2, default=0.0
    )
    is_external = models.BooleanField("Realizado por Tercero", default=False)
    labor_rate = models.DecimalField(
        "Tarifa o Costo Fijo (Tercero)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    evidence_urls = models.JSONField("URLs de Evidencias", default=list, blank=True)

    def __str__(self) -> str:
        """Return description or subcategory string."""

        return str(self.subcategory) if self.subcategory else self.description

    class Meta:
        verbose_name = "Trabajo Adicional de OT"
        verbose_name_plural = "Trabajos Adicionales de OT"


class WorkOrderPart(models.Model):
    """Part used within a work order."""

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="parts_used")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, verbose_name="Repuesto")
    quantity = models.DecimalField(
        "Cantidad Usada", max_digits=10, decimal_places=2, default=1.0
    )
    cost_at_moment = models.DecimalField(
        "Costo al Momento de Uso", max_digits=10, decimal_places=2
    )

    class Meta:
        unique_together = ("work_order", "part")
        verbose_name = "Repuesto Usado en OT"
        verbose_name_plural = "Repuestos Usados en OT"


# --- NUEVO: Conectores de Señales (Signals) ---
@receiver([post_save, post_delete], sender=WorkOrderTask)
def on_task_change(sender, instance, **kwargs):
    """Recalculate costs when a task is added or removed."""

    instance.work_order.recalculate_costs()


@receiver([post_save, post_delete], sender=WorkOrderPart)
def on_part_change(sender, instance, **kwargs):
    """Recalculate costs when a part is added or removed."""

    instance.work_order.recalculate_costs()

