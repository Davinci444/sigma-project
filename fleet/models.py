# fleet/models.py
from django.db import models
from core.models import Zone

class Vehicle(models.Model):
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
    
    plate = models.CharField("Placa", max_length=10, unique=True)
    vin = models.CharField("VIN", max_length=17, unique=True, blank=True, null=True)
    brand = models.CharField("Marca", max_length=50)
    model = models.CharField("Modelo", max_length=50)
    year = models.PositiveIntegerField("Año")
    vehicle_type = models.CharField("Tipo de Vehículo", max_length=50, help_text="Ej: Camión, Auto, Moto")
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
        # Antes de guardar, limpiamos la placa
        self.plate = self.plate.upper().strip().replace('-', '')
        super().save(*args, **kwargs) # Llamamos al método de guardado original

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate})"
    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['plate']

class VehicleZoneHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="zone_history")
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT)
    start_date = models.DateField("Fecha de Inicio en Zona")
    end_date = models.DateField("Fecha de Fin en Zona", null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle.plate} en {self.zone.name} desde {self.start_date}"
    class Meta:
        verbose_name = "Historial de Zona del Vehículo"
        verbose_name_plural = "Historiales de Zona de Vehículos"
        ordering = ['-start_date']