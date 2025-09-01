"""Models for managing inventory, suppliers y repuestos por vehículo."""
from django.db import models


# =========================
# PROVEEDORES / INVENTARIO BASE (lo que ya manejas)
# =========================

class Supplier(models.Model):
    name = models.CharField("Nombre del Proveedor", max_length=150)
    nit = models.CharField("NIT", max_length=20, unique=True, blank=True, null=True)
    contact_person = models.CharField("Persona de Contacto", max_length=100, blank=True)
    phone = models.CharField("Teléfono", max_length=30, blank=True)
    email = models.EmailField("Correo", blank=True)
    address = models.CharField("Dirección", max_length=255, blank=True)
    notes = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self) -> str:
        return self.name


class Part(models.Model):
    sku = models.CharField("SKU", max_length=50, unique=True)
    name = models.CharField("Nombre", max_length=150)
    description = models.TextField("Descripción", blank=True)
    quantity = models.DecimalField("Cantidad", max_digits=10, decimal_places=2, default=0)
    unit = models.CharField("Unidad", max_length=32, blank=True)
    minimal_stock = models.DecimalField("Stock Mínimo", max_digits=10, decimal_places=2, default=0)

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parts",
        verbose_name="Proveedor",
    )

    class Meta:
        verbose_name = "Repuesto (Inventario)"
        verbose_name_plural = "Repuestos (Inventario)"

    def __str__(self) -> str:
        return f"{self.sku} - {self.name}"


class InventoryMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = "IN", "Entrada"
        OUT = "OUT", "Salida"

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name="Repuesto",
    )
    movement_type = models.CharField(
        "Tipo", max_length=3, choices=MovementType.choices, default=MovementType.IN
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

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self) -> str:
        return f"{self.movement_type} de {self.quantity} x {self.part.sku}"


# =========================
# NUEVO: CATÁLOGO DE REPUESTOS
# =========================

class SpareCategory(models.Model):
    name = models.CharField("Nombre de categoría", max_length=80, unique=True)
    slug = models.SlugField("Slug", max_length=100, unique=True)
    description = models.TextField("Descripción", blank=True)
    is_active = models.BooleanField("Activa", default=True)

    class Meta:
        verbose_name = "Categoría de repuesto"
        verbose_name_plural = "Categorías de repuestos"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SpareItem(models.Model):
    category = models.ForeignKey(
        SpareCategory, on_delete=models.PROTECT, related_name="items", verbose_name="Categoría"
    )
    name = models.CharField("Nombre (genérico)", max_length=120)
    description = models.TextField("Descripción", blank=True)
    unit = models.CharField("Unidad", max_length=32, blank=True)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Ítem de repuesto"
        verbose_name_plural = "Ítems de repuesto"
        ordering = ["category__name", "name"]
        unique_together = (("category", "name"),)

    def __str__(self):
        return f"{self.category.name} · {self.name}"


# =========================
# NUEVO: REPUESTOS VINCULADOS A CADA VEHÍCULO
# =========================

class VehicleSpare(models.Model):
    vehicle = models.ForeignKey(
        "fleet.Vehicle", on_delete=models.CASCADE, related_name="spares", verbose_name="Vehículo"
    )
    spare_item = models.ForeignKey(
        SpareItem, on_delete=models.PROTECT, related_name="vehicle_links", verbose_name="Ítem"
    )

    brand = models.CharField("Marca", max_length=120, blank=True)
    part_number = models.CharField("Referencia / Part number", max_length=120, blank=True)
    quantity = models.DecimalField("Cantidad", max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField("Notas", blank=True)

    last_replacement_date = models.DateField("Último reemplazo", blank=True, null=True)
    next_replacement_km = models.PositiveIntegerField("Próximo reemplazo (km)", blank=True, null=True)

    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        verbose_name = "Repuesto del vehículo"
        verbose_name_plural = "Repuestos del vehículo"
        ordering = ["vehicle__plate", "spare_item__category__name", "spare_item__name"]

    def __str__(self):
        return f"{self.vehicle.plate} · {self.spare_item}"
