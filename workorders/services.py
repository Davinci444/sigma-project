"""Service utilities for workorders app."""

from .models import MaintenanceManual, ManualTask


def calc_next_due(vehicle, plan):
    """Calculate next preventive maintenance target in km and description."""
    manual = plan.manual or MaintenanceManual.objects.filter(fuel_type=vehicle.fuel_type).first()
    if not manual:
        return None, None

    tasks = list(ManualTask.objects.filter(manual=manual).order_by("km_interval"))
    if not tasks:
        return None, None

    base_km = plan.last_service_km or 0
    current_km = vehicle.current_odometer_km or 0
    delta = max(0, current_km - base_km)

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
