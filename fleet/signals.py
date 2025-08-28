# fleet/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vehicle
from workorders.models import MaintenancePlan, MaintenanceManual

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Vehicle)
def assign_maintenance_plan_on_vehicle_creation(sender, instance, created, **kwargs):
    """
    Asigna automáticamente un plan de mantenimiento cuando se crea un vehículo.

    - Si el vehículo ya tiene plan, no hace nada.
    - Solo actúa cuando el vehículo se crea y tiene `fuel_type` definido.
    """

    # Evitar duplicados
    if MaintenancePlan.objects.filter(vehicle=instance).exists():
        return

    # Solo al crear y si tiene tipo de combustible
    if not (created and instance.fuel_type):
        return

    try:
        manual = MaintenanceManual.objects.get(fuel_type=instance.fuel_type)
    except MaintenanceManual.DoesNotExist:
        logger.warning(
            "No existe manual para fuel_type=%s (vehículo %s).",
            instance.fuel_type, instance.plate
        )
        return
    except MaintenanceManual.MultipleObjectsReturned:
        # Si hay varios, tomar el primero determinísticamente y advertir
        manual = (
            MaintenanceManual.objects
            .filter(fuel_type=instance.fuel_type)
            .order_by("id")
            .first()
        )
        logger.warning(
            "Múltiples manuales para fuel_type=%s; usando '%s' (vehículo %s).",
            instance.fuel_type,
            manual.name if manual else "N/A",
            instance.plate
        )
        if manual is None:
            return

    # Crear plan de mantenimiento
    MaintenancePlan.objects.create(vehicle=instance, manual=manual)
    logger.info(
        "Plan de mantenimiento '%s' asignado automáticamente a %s.",
        manual.name, instance.plate
    )
