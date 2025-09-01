"""Models for managing fleet vehicles and their zone history."""

from django.db import models
from core.models import Zone

class Vehicle(models.Model):
    """Represents a fleet vehicle.

    Key fields include the unique ``plate`` and ``vin`` identifiers, the
    vehicle's ``status``, and its current operational ``current_zone``.
    """
    class VehicleStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        IN_REPAIR = 'IN_REPAIR', 'En Reparación'
        SOLD = 'SOLD', 'Vendido'
        INACTIVE = 'INACTIVE', 'Inactivo'

    class FuelType(models.TextChoices):
        GASOLINE = 'GASOLINE', 'Gasolina'
        DIESEL = 'DIESEL', 'Diésel'

    class OdometerStatus(models.TextChoices):
        VALID = 'VALID', 'Válido'
        INVALID = 'INVALID', 'Inválido (Reportado en Novedades)'

    class VehicleType(models.TextChoices):
        AUTOMOVIL = 'AUTOMOVIL', 'Automóvil'
        MICROBUS = 'MICROBUS', 'Microbús'
        BUS = 'BUS', 'Bus'

    
    plate = models.CharField("Placa", max_length=10, unique=True)
    vin = models.CharField("VIN", max_length=17, unique=True, blank=True, null=True)
    brand = models.CharField("Marca", max_length=50)
    linea = models.CharField("Línea", max_length=50)
    modelo = models.PositiveIntegerField("Modelo")
    vehicle_type = models.CharField(
        "Tipo de Vehículo",
        max_length=10,
        choices=VehicleType.choices,
        help_text="Seleccione el tipo de vehículo",
    )
    fuel_type = models.CharField("Tipo de Combustible", max_length=20, choices=FuelType.choices, default=FuelType.DIESEL)
    status = models.CharField("Estado", max_length=20, choices=VehicleStatus.choices, default=VehicleStatus.ACTIVE)
    
    current_zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zona Operativa Actual")

    current_odometer_km = models.PositiveIntegerField("Kilometraje Actual (km)", default=0, help_text="Última lectura válida del odómetro.")
    odometer_status = models.CharField("Estado del Odómetro", max_length=20, choices=OdometerStatus.choices, default=OdometerStatus.VALID)
    soat_due_date = models.DateField("Vencimiento SOAT", blank=True, null=True)
    rtm_due_date = models.DateField("Vencimiento RTM", blank=True, null=True)
    notes = models.TextField("Notas Adicionales", blank=True)

    # --- NUEVA LÓGICA DE AUTOLIMPIEZA ---
    def save(self, *args, **kwargs):
        """Normalize the plate before saving.

        Args:
            *args: Positional arguments for ``Model.save``.
            **kwargs: Keyword arguments for ``Model.save``.
        """
        # Antes de guardar, limpiamos la placa
        self.plate = self.plate.upper().strip().replace('-', '')
        super().save(*args, **kwargs)  # Llamamos al método de guardado original

    def __str__(self):
        return f"{self.brand} {self.linea} ({self.plate})"
    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['plate']

class VehicleZoneHistory(models.Model):
    """Tracks a vehicle's zone assignments over time.

    Records the ``zone`` where the vehicle was located along with the
    ``start_date`` and optional ``end_date`` for each assignment.
    """

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="zone_history"
    )
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT)
    start_date = models.DateField("Fecha de Inicio en Zona")
    end_date = models.DateField("Fecha de Fin en Zona", null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle.plate} en {self.zone.name} desde {self.start_date}"
    class Meta:
        verbose_name = "Historial de Zona del Vehículo"
        verbose_name_plural = "Historiales de Zona de Vehículos"
        ordering = ['-start_date']


from .fuel_logs import FuelUploadLog  # noqa: F401  # Import para registrar el modelo
