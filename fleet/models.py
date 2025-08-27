# fleet/models.py

from django.db import models

class Vehicle(models.Model):
    # Estados posibles para el vehículo
    class VehicleStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        IN_REPAIR = 'IN_REPAIR', 'En Reparación'
        SOLD = 'SOLD', 'Vendido'
        INACTIVE = 'INACTIVE', 'Inactivo'

    # Tipos de combustible
    class FuelType(models.TextChoices):
        GASOLINE = 'GASOLINE', 'Gasolina'
        DIESEL = 'DIESEL', 'Diésel'
        ELECTRIC = 'ELECTRIC', 'Eléctrico'
        HYBRID = 'HYBRID', 'Híbrido'
        GAS = 'GAS', 'Gas'

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