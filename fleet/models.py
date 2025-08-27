# fleet/models.py

from django.db import models

class Vehicle(models.Model):
    # (Los estados y tipos de combustible se quedan igual)
    class VehicleStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        IN_REPAIR = 'IN_REPAIR', 'En Reparación'
        SOLD = 'SOLD', 'Vendido'
        INACTIVE = 'INACTIVE', 'Inactivo'

    class FuelType(models.TextChoices):
        GASOLINE = 'GASOLINE', 'Gasolina'
        DIESEL = 'DIESEL', 'Diésel'
        ELECTRIC = 'ELECTRIC', 'Eléctrico'
        HYBRID = 'HYBRID', 'Híbrido'
        GAS = 'GAS', 'Gas'

    # --- NUEVO CAMPO ---
    class OdometerStatus(models.TextChoices):
        VALID = 'VALID', 'Válido'
        INVALID = 'INVALID', 'Inválido (Reportado en Novedades)'

    # Información básica
    plate = models.CharField("Placa", max_length=10, unique=True)
    vin = models.CharField("VIN", max_length=17, unique=True, blank=True, null=True)
    brand = models.CharField("Marca", max_length=50)
    model = models.CharField("Modelo", max_length=50)
    year = models.PositiveIntegerField("Año")
    
    # Clasificación y estado
    vehicle_type = models.CharField("Tipo de Vehículo", max_length=50, help_text="Ej: Camión, Auto, Moto")
    fuel_type = models.CharField("Tipo de Combustible", max_length=20, choices=FuelType.choices, default=FuelType.DIESEL)
    status = models.CharField("Estado", max_length=20, choices=VehicleStatus.choices, default=VehicleStatus.ACTIVE)

    # --- NUEVOS CAMPOS ---
    # Guardará el último kilometraje válido conocido del vehículo.
    current_odometer_km = models.PositiveIntegerField("Kilometraje Actual (km)", default=0, help_text="Última lectura válida del odómetro.")
    odometer_status = models.CharField("Estado del Odómetro", max_length=20, choices=OdometerStatus.choices, default=OdometerStatus.VALID)

    # Documentación
    soat_due_date = models.DateField("Vencimiento SOAT", blank=True, null=True)
    rtm_due_date = models.DateField("Vencimiento RTM", blank=True, null=True)
    
    notes = models.TextField("Notas Adicionales", blank=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate})"

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['plate']