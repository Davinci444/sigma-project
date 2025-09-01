"""Models for managing maintenance plans and work orders."""

from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from fleet.models import Vehicle
from inventory.models import Part


# -----------------------------
# Manual / Plan Preventivo
# -----------------------------
class MaintenanceManual(models.Model):
    """Manual de mantenimiento por tipo de combustible."""

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
        return self.name

    class Meta:
        verbose_name = "Manual de Mantenimiento"
        verbose_name_plural = "Manuales de Mantenimiento"


class ManualTask(models.Model):
    """Tarea definida dentro de un manual."""

    manual = models.ForeignKey(
        MaintenanceManual, on_delete=models.CASCADE, related_name="tasks"
    )
    km_interval = models.PositiveIntegerField(
        "Hito de Kilometraje (km)", help_text="Ej: 10000, 20000, 40000"
    )
    description = models.CharField("Descripción de la Tarea", max_length=255)

    def __str__(self) -> str:
        return f"A los {self.km_interval} km: {self.description}"

    class Meta:
        verbose_name = "Tarea de Manual"
        verbose_name_plural = "Tareas de Manual"
        ordering = ["km_interval"]


class MaintenancePlan(models.Model):
    """Asocia un vehículo con un manual de mantenimiento."""

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
        manual_name = self.manual.name if self.manual else "N/A"
        return f"Plan para {self.vehicle.plate} (basado en {manual_name})"

    class Meta:
        verbose_name = "Plan de Mantenimiento"
        verbose_name_plural = "Planes de Mantenimiento"


# -----------------------------
# Taxonomía de Mantenimiento
# -----------------------------
class MaintenanceCategory(models.Model):
    name = models.CharField("Nombre de la Categoría", max_length=100, unique=True)
    description = models.TextField("Descripción", blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Categoría de Mantenimiento"
        verbose_name_plural = "Categorías de Mantenimiento"


class MaintenanceSubcategory(models.Model):
    category = models.ForeignKey(
        MaintenanceCategory,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name="Categoría Principal",
    )
    name = models.CharField("Nombre de la Subcategoría", max_length=100)
    description = models.TextField("Descripción", blank=True)

    def __str__(self) -> str:
        return f"{self.category.name} -> {self.name}"

    class Meta:
        verbose_name = "Subcategoría de Mantenimiento"
        verbose_name_plural = "Subcategorías de Mantenimiento"
        unique_together = ("category", "name")


# -----------------------------
# Causas probables (correctivo)
# -----------------------------
class ProbableCause(models.Model):
    name = models.CharField("Nombre", max_length=120, unique=True)
    description = models.TextField("Descripción", blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Causa Probable"
        verbose_name_plural = "Causas Probables"
        ordering = ["name"]


# -----------------------------
# OT
# -----------------------------
class WorkOrder(models.Model):
    """Orden de trabajo (preventivo o correctivo)."""

    class OrderType(models.TextChoices):
        PREVENTIVE = "PREVENTIVE", "Preventivo"
        CORRECTIVE = "CORRECTIVE", "Correctivo"

    class OrderStatus(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Programada"
        WAITING_PART = "WAITING_PART", "Espera Repuesto"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        IN_ROAD_TEST = "IN_ROAD_TEST", "Prueba de Ruta"
        COMPLETED = "COMPLETED", "Completada"

    class Priority(models.TextChoices):
        LOW = "LOW", "Baja"
        MEDIUM = "MEDIUM", "Media"
        HIGH = "HIGH", "Alta"
        URGENT = "URGENT", "Urgente"

    class FailureOrigin(models.TextChoices):
        MISUSE = "MISUSE", "Mal uso / Operación"
        WEAR = "WEAR", "Desgaste normal"
        ROUTE = "ROUTE", "Condiciones de ruta"
        MANUFACTURING = "MANUFACTURING", "Falla de fabricación"
        MAINTENANCE = "MAINTENANCE", "Mantenimiento previo deficiente"
        OTHER = "OTHER", "Otro"

    class Severity(models.TextChoices):
        MINOR = "MINOR", "Leve"
        MODERATE = "MODERATE", "Moderada"
        HIGH = "HIGH", "Alta"
        CRITICAL = "CRITICAL", "Crítica"

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

    # Conductores responsables (M2M con through)
    drivers = models.ManyToManyField(
        "users.Driver",
        verbose_name="Conductores responsables",
        blank=True,
        related_name="work_orders",
        through="WorkOrderDriver",
    )

    # Datos generales
    description = models.TextField("Descripción del Problema/Trabajo Principal")
    scheduled_start = models.DateTimeField("Inicio Programado", null=True, blank=True)
    scheduled_end = models.DateTimeField("Fin Programado (Estimado)", null=True, blank=True)
    check_in_at = models.DateTimeField("Ingreso Real", null=True, blank=True)
    check_out_at = models.DateTimeField("Salida Real", null=True, blank=True)
    odometer_at_service = models.PositiveIntegerField(
        "Kilometraje al Ingresar", null=True, blank=True,
        help_text="KM del vehículo al momento de esta OT",
    )

    # Campos de costos (calculados vía señales)
    labor_cost_internal = models.DecimalField("Costo MO Interna", max_digits=10, decimal_places=2, default=0.0)
    labor_cost_external = models.DecimalField("Costo MO Terceros", max_digits=10, decimal_places=2, default=0.0)
    parts_cost = models.DecimalField("Costo Repuestos", max_digits=10, decimal_places=2, default=0.0)

    created_at = models.DateTimeField("Fecha de Creación", auto_now_add=True)

    # -----------------------
    # Campos Correctivo
    # -----------------------
    pre_diagnosis = models.TextField("Pre-diagnóstico", blank=True)
    failure_origin = models.CharField(
        "Origen de la falla", max_length=20, choices=FailureOrigin.choices, null=True, blank=True
    )
    severity = models.CharField(
        "Severidad", max_length=12, choices=Severity.choices, null=True, blank=True
    )
    requires_approval = models.BooleanField("Requiere aprobación", default=False)
    out_of_service = models.BooleanField("Vehículo fuera de servicio", default=False)
    warranty_covered = models.BooleanField("Cubre garantía", default=False)
    probable_causes = models.ManyToManyField(
        ProbableCause, blank=True, related_name="work_orders", verbose_name="Causas probables"
    )

    def __str__(self) -> str:
        return f"OT-{self.id} ({self.get_order_type_display()}) para {self.vehicle.plate}"

    def recalculate_costs(self) -> None:
        """Recalcular costos en base a tareas y repuestos."""
        labor_costs = self.tasks.aggregate(
            internal=Sum("hours_spent", filter=Q(is_external=False)),
            external=Sum("labor_rate", filter=Q(is_external=True)),
        )
        internal_rate = settings.WORKORDER_INTERNAL_RATE
        self.labor_cost_internal = (labor_costs["internal"] or 0) * internal_rate
        self.labor_cost_external = labor_costs["external"] or 0

        parts_total = self.parts_used.aggregate(
            total=Sum(ExpressionWrapper(F("quantity") * F("cost_at_moment"), output_field=DecimalField()))
        )["total"]
        self.parts_cost = parts_total or 0

        self.save(update_fields=["labor_cost_internal", "labor_cost_external", "parts_cost"])

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = ["-created_at"]


class WorkOrderTask(models.Model):
    """Trabajo / actividad dentro de una OT."""

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="Orden de Trabajo"
    )
    category = models.ForeignKey(
        MaintenanceCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría"
    )
    subcategory = models.ForeignKey(
        MaintenanceSubcategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subcategoría"
    )
    description = models.CharField("Descripción del Trabajo", max_length=255, blank=True)
    hours_spent = models.DecimalField("Horas Invertidas", max_digits=5, decimal_places=2, default=0.0)
    is_external = models.BooleanField("Realizado por Tercero", default=False)
    labor_rate = models.DecimalField(
        "Tarifa o Costo Fijo (Tercero)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    # Nota: mantenemos el JSON de URLs (histórico); evidencias por archivo vendrán en otra fase
    evidence_urls = models.JSONField("URLs de Evidencias", default=list, blank=True)

    def __str__(self) -> str:
        return str(self.subcategory) if self.subcategory else self.description

    class Meta:
        verbose_name = "Trabajo Adicional de OT"
        verbose_name_plural = "Trabajos Adicionales de OT"


class WorkOrderPart(models.Model):
    """Repuesto usado en una OT."""

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="parts_used")
    part = models.ForeignKey(Part, on_delete=models.PROTECT, verbose_name="Repuesto")
    quantity = models.DecimalField("Cantidad Usada", max_digits=10, decimal_places=2, default=1.0)
    cost_at_moment = models.DecimalField("Costo al Momento de Uso", max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("work_order", "part")
        verbose_name = "Repuesto Usado en OT"
        verbose_name_plural = "Repuestos Usados en OT"


class WorkOrderAttachment(models.Model):
    """Adjuntos simples (URL) a nivel de OT (histórico)."""

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="attachments")
    url = models.URLField("URL")
    description = models.CharField("Descripción", max_length=200, blank=True)
    created_at = models.DateTimeField("Fecha", auto_now_add=True)

    class Meta:
        verbose_name = "Adjunto de OT"
        verbose_name_plural = "Adjuntos de OT"
        ordering = ["-created_at"]


class WorkOrderDriver(models.Model):
    """Tabla intermedia para responsables (conductores) en una OT."""

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="driver_links")
    driver = models.ForeignKey("users.Driver", on_delete=models.PROTECT, related_name="work_order_links")
    responsibility_percent = models.DecimalField(
        "Responsabilidad (%)", max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Responsable en OT"
        verbose_name_plural = "Responsables en OT"
        unique_together = (("work_order", "driver"),)


class WorkOrderNote(models.Model):
    """Novedades/comentarios con visibilidad (Todos/Gerencia)."""

    class Visibility(models.TextChoices):
        ALL = "ALL", "Todos"
        MGMT_ONLY = "MGMT_ONLY", "Solo Gerencia"

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="notes")
    visibility = models.CharField("Visibilidad", max_length=10, choices=Visibility.choices, default=Visibility.ALL)
    text = models.TextField("Comentario / Novedad")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("Fecha", auto_now_add=True)

    class Meta:
        verbose_name = "Novedad de OT"
        verbose_name_plural = "Novedades de OT"
        ordering = ["-created_at"]


# -----------------------------
# Señales: costos al vuelo
# -----------------------------
@receiver([post_save, post_delete], sender=WorkOrderTask)
def on_task_change(sender, instance, **kwargs):
    instance.work_order.recalculate_costs()


@receiver([post_save, post_delete], sender=WorkOrderPart)
def on_part_change(sender, instance, **kwargs):
    instance.work_order.recalculate_costs()


