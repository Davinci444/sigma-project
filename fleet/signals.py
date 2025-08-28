# fleet/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction, IntegrityError
from .models import Vehicle
from workorders.models import MaintenancePlan, MaintenanceManual

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Vehicle)
def assign_maintenance_plan_on_vehicle_creation(sender, instance, created, **kwargs):
    """
    Asigna automáticamente un plan de mantenimiento cuando se crea un vehículo.

    - Si el vehículo ya tiene plan, no hace nada.
    - Solo actúa cuando el vehículo se crea y tiene `fuel_type` definido.
    - Usa transacción para evitar duplicados en situaciones de concurrencia.
    """

    if not (created and instance.fuel_type):
        return

    try:
        with transaction.atomic():
            manual = (
                MaintenanceManual.objects
                .filter(fuel_type=instance.fuel_type)
                .order_by("id")
                .first()
            )

            if not manual:
                logger.warning(
                    "No existe manual para fuel_type=%s (vehículo %s).",
                    instance.fuel_type, instance.plate
                )
                return

            plan, created_plan = MaintenancePlan.objects.get_or_create(
                vehicle=instance, defaults={"manual": manual}
            )

            if created_plan:
                logger.info(
                    "Plan de mantenimiento '%s' asignado automáticamente a %s.",
                    manual.name, instance.plate
                )
            else:
                logger.info(
                    "El vehículo %s ya tenía plan de mantenimiento asignado.",
                    instance.plate
                )

    except IntegrityError:
        logger.warning(
            "Condición de carrera detectada al asignar plan a %s, se ignoró duplicado.",
            instance.plate
        )
