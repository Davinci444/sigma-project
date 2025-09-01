# workorders/signals_extra.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import WorkOrder, MaintenancePlan, MaintenanceManual, ManualTask
from core.models import Alert

def _calc_next_due(vehicle, plan):
    """
    Calcula próximo mantenimiento sugerido (km objetivo y descripción) usando el manual asociado.
    """
    manual = plan.manual or MaintenanceManual.objects.filter(fuel_type=vehicle.fuel_type).first()
    if not manual:
        return None, None

    tasks = list(ManualTask.objects.filter(manual=manual).order_by("km_interval"))
    if not tasks:
        return None, None

    base_km = plan.last_service_km or 0
    current_km = vehicle.current_odometer_km or 0
    delta = max(0, current_km - base_km)

    # próxima tarea >= delta; si no hay, usar período
    next_task = next((t for t in tasks if t.km_interval >= delta), None)
    if next_task:
        next_due_km = base_km + next_task.km_interval
        desc = next_task.description
    else:
        period = tasks[0].km_interval or 10000
        multiples = (delta // period) + 1
        next_due_km = base_km + multiples * period
        desc = f"Ciclo cada {period} km"

    return next_due_km, desc

@receiver(post_save, sender=WorkOrder)
def update_plan_and_alert_on_preventive_close(sender, instance: WorkOrder, created, **kwargs):
    """
    Cuando una OT Preventiva queda COMPLETED:
    - Activa/actualiza el MaintenancePlan.
    - Calcula y crea/actualiza una alerta PREVENTIVE_DUE con el próximo hito.
    """
    try:
        if instance.order_type != WorkOrder.OrderType.PREVENTIVE:
            return
        if instance.status != WorkOrder.OrderStatus.COMPLETED:
            return

        vehicle = instance.vehicle
        plan, _ = MaintenancePlan.objects.get_or_create(
            vehicle=vehicle,
            defaults={"manual": MaintenanceManual.objects.filter(fuel_type=vehicle.fuel_type).first()}
        )
        plan.is_active = True
        # preferimos el odómetro registrado en la OT; si no, usamos el actual del vehículo
        plan.last_service_km = instance.odometer_at_service or (vehicle.current_odometer_km or 0)
        plan.last_service_date = timezone.now().date()
        plan.save()

        # Crear/actualizar alerta
        next_due_km, desc = _calc_next_due(vehicle, plan)
        if next_due_km is None:
            return

        km_to_due = next_due_km - (vehicle.current_odometer_km or 0)
        severity = (Alert.Severity.CRITICAL if km_to_due <= 0
                    else Alert.Severity.WARNING if km_to_due <= 500
                    else Alert.Severity.INFO)
        msg = f"Próximo preventivo para {vehicle.plate} a los {next_due_km} km ({max(0, km_to_due)} km restantes): {desc}"

        qs = Alert.objects.filter(alert_type=Alert.AlertType.PREVENTIVE_DUE, related_vehicle=vehicle, seen=False)
        alert = qs.first()
        if alert:
            alert.severity = severity
            alert.message = msg
            alert.save(update_fields=["severity","message"])
        else:
            Alert.objects.create(
                alert_type=Alert.AlertType.PREVENTIVE_DUE,
                related_vehicle=vehicle,
                severity=severity,
                message=msg,
                seen=False,
            )
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Error en señal de preventivo cerrado")
