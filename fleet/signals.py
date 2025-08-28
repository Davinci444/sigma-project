"""Signal handlers for the fleet application."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vehicle
from workorders.models import MaintenancePlan, MaintenanceManual


@receiver(post_save, sender=Vehicle)
def assign_maintenance_plan_on_vehicle_creation(sender, instance, created, **kwargs):
    """Assign a maintenance plan when a vehicle is created.

    Args:
        sender (Model): The model class sending the signal.
        instance (Vehicle): The instance being saved.
        created (bool): Indicates if the instance was created.
        **kwargs: Additional keyword arguments.
    """

    # Verificamos si el vehículo ya tiene un plan
    if MaintenancePlan.objects.filter(vehicle=instance).exists():
        return

    # Si es un vehículo nuevo o no tiene plan, buscamos el manual correcto
    if instance.fuel_type and created:
        try:
            manual = MaintenanceManual.objects.get(fuel_type=instance.fuel_type)
            MaintenancePlan.objects.create(vehicle=instance, manual=manual)
            print(
                f"Plan de mantenimiento '{manual.name}' asignado automáticamente a {instance.plate}."
            )
        except MaintenanceManual.DoesNotExist:
            pass

