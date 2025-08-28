# fleet/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vehicle
from workorders.models import MaintenancePlan, MaintenanceManual

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Vehicle)
def assign_maintenance_plan_on_vehicle_creation(sender, instance, created, **kwargs):
    """Asignar un plan de mantenimiento cuando se crea un vehículo."""
    # Si ya tiene plan, no hacer nada
    if MaintenancePlan.objects.filter(vehicle=instance).exists():
        return

<<<<<<< HEAD
    # Si es un vehículo nuevo o no tiene plan, buscamos el manual correcto
    if instance.fuel_type:
        try:
            # Buscamos un manual que coincida con el tipo de combustible
            manual = MaintenanceManual.objects.get(fuel_type=instance.fuel_type)
            
            # Creamos el plan "dormido", enlazando el vehículo con el manual
            MaintenancePlan.objects.create(vehicle=instance, manual=manual)
            logger.info(
                "Plan de mantenimiento '%s' asignado automáticamente a %s.",
                manual.name,
                instance.plate,
            )
        except MaintenanceManual.DoesNotExist:
            # No hacemos nada si no hay un manual para ese tipo de combustible
            pass
=======
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
        # Si hay varios, toma el primero y avisa
        manual = (MaintenanceManual.objects
                  .filter(fuel_type=instance.fuel_type)
                  .order_by('id')
                  .first())
        logger.warning(
            "Múltiples manuales para fuel_type=%s; usando '%s' (vehículo %s).",
            instance.fuel_type, manual.name if manual else "N/A", instance.plate
        )
        if manual is None:
            return

    MaintenancePlan.objects.create(vehicle=instance, manual=manual)
    logger.info(
        "Plan de mantenimiento '%s' asignado automáticamente a %s.",
        manual.name, instance.plate
    )
>>>>>>> 33c8074 (Optimizando codigo para mejor rendimiento)
