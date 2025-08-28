# fleet/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vehicle
from workorders.models import MaintenancePlan, MaintenanceManual


@receiver(post_save, sender=Vehicle)
def assign_maintenance_plan_on_vehicle_creation(sender, instance, created, **kwargs):
    """
    Señal que se dispara después de guardar un Vehículo.
    Asigna automáticamente un plan de mantenimiento si no tiene uno.
    """
    # Verificamos si el vehículo ya tiene un plan
    if MaintenancePlan.objects.filter(vehicle=instance).exists():
        return

    # Si es un vehículo nuevo o no tiene plan, buscamos el manual correcto
    if instance.fuel_type:
        try:
            # Buscamos un manual que coincida con el tipo de combustible
            manual = MaintenanceManual.objects.get(fuel_type=instance.fuel_type)

            # Creamos el plan "dormido", enlazando el vehículo con el manual
            MaintenancePlan.objects.create(vehicle=instance, manual=manual)
            print(
                f"Plan de mantenimiento '{manual.name}' asignado automáticamente a {instance.plate}."
            )
        except MaintenanceManual.DoesNotExist:
            # No hacemos nada si no hay un manual para ese tipo de combustible
            pass
