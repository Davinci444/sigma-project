# inventory/models.py

from django.db import models

class Supplier(models.Model):
    name = models.CharField("Nombre del Proveedor", max_length=150)
    nit = models.CharField("NIT", max_length=20, unique=True, blank=True, null=True)
    contact_person = models.CharField("Persona de Contacto", max_length=100, blank=True)
    phone = models.CharField("Teléfono", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


class Part(models.Model):
    sku = models.CharField("SKU (Referencia)", max_length=50, unique=True)
    name = models.CharField("Nombre del Repuesto", max_length=200)
    description = models.TextField("Descripción", blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    location = models.CharField("Ubicación en Bodega", max_length=100, blank=True)
    
    stock_current = models.PositiveIntegerField("Stock Actual", default=0)
    stock_min = models.PositiveIntegerField("Stock Mínimo", default=1)
    
    average_cost = models.DecimalField("Costo Promedio", max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"


class InventoryMovement(models.Model):
    class MovementType(models.TextChoices):
        INBOUND = 'INBOUND', 'Entrada'
        OUTBOUND = 'OUTBOUND', 'Salida'
        ADJUSTMENT = 'ADJUSTMENT', 'Ajuste'

    part = models.ForeignKey(Part, on_delete=models.CASCADE, verbose_name="Repuesto")
    movement_type = models.CharField("Tipo de Movimiento", max_length=20, choices=MovementType.choices)
    quantity = models.PositiveIntegerField("Cantidad")
    # Referencia a la OT que causó la salida de inventario
    work_order = models.ForeignKey('workorders.WorkOrder', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Orden de Trabajo")
    reason = models.CharField("Motivo del movimiento", max_length=255, blank=True, help_text="Ej: Compra inicial, Consumo en OT, Ajuste por inventario físico")
    timestamp = models.DateTimeField("Fecha y Hora", auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} de {self.quantity} x {self.part.sku}"

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"