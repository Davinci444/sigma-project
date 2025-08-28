"""Models for managing inventory and suppliers."""

from django.db import models


class Supplier(models.Model):
    """Represents a supplier of parts."""

    name = models.CharField("Nombre del Proveedor", max_length=150)
    nit = models.CharField("NIT", max_length=20, unique=True, blank=True, null=True)
    contact_person = models.CharField("Persona de Contacto", max_length=100, blank=True)
    phone = models.CharField("Teléfono", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)

    def __str__(self) -> str:
        """Return supplier name."""

        return self.name

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


class Part(models.Model):
    """Represents an inventory part."""

    class UnitOfMeasure(models.TextChoices):
        UNIT = "UNIT", "Unidad"
        LITER = "LITER", "Litro"
        GALLON = "GALLON", "Galón"
        METER = "METER", "Metro"
        SET = "SET", "Juego/Kit"

    sku = models.CharField("SKU (Referencia)", max_length=50, unique=True)
    name = models.CharField("Nombre del Repuesto", max_length=200)
    description = models.TextField("Descripción", blank=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor"
    )
    location = models.CharField("Ubicación en Bodega", max_length=100, blank=True)

    # --- NUEVO CAMPO ---
    unit = models.CharField(
        "Unidad de Medida",
        max_length=20,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.UNIT,
    )

    stock_current = models.DecimalField("Stock Actual", max_digits=10, decimal_places=2, default=0.0)
    stock_min = models.DecimalField("Stock Mínimo", max_digits=10, decimal_places=2, default=1.0)
    average_cost = models.DecimalField("Costo Promedio", max_digits=10, decimal_places=2, default=0.0)

    def __str__(self) -> str:
        """Return part name and SKU."""

        return f"{self.name} ({self.sku})"

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"


class InventoryMovement(models.Model):
    """Tracks movements of parts in inventory."""

    class MovementType(models.TextChoices):
        INBOUND = "INBOUND", "Entrada"
        OUTBOUND = "OUTBOUND", "Salida"
        ADJUSTMENT = "ADJUSTMENT", "Ajuste"

    part = models.ForeignKey(Part, on_delete=models.CASCADE, verbose_name="Repuesto")
    movement_type = models.CharField(
        "Tipo de Movimiento", max_length=20, choices=MovementType.choices
    )
    quantity = models.DecimalField("Cantidad", max_digits=10, decimal_places=2)
    work_order = models.ForeignKey(
        "workorders.WorkOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Orden de Trabajo",
    )
    reason = models.CharField("Motivo del movimiento", max_length=255, blank=True)
    timestamp = models.DateTimeField("Fecha y Hora", auto_now_add=True)

    def __str__(self) -> str:
        """Return description of the movement."""

        return f"{self.movement_type} de {self.quantity} x {self.part.sku}"

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

