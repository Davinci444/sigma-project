# reports/views.py
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.db.models import Sum, F

from fleet.models import Vehicle
from workorders.models import WorkOrder, MaintenancePlan


@user_passes_test(lambda u: u.is_superuser)
def vehicle_costs_report(request):
    # ... (código del reporte de costos sin cambios)
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="reporte_costos_vehiculos_{timezone.now().strftime("%Y-%m-%d")}.csv"'
        },
    )
    response.write("\ufeff".encode("utf8"))
    writer = csv.writer(response)
    writer.writerow(
        [
            "Placa",
            "Marca",
            "Modelo",
            "Año",
            "Costo Total MO Interna",
            "Costo Total MO Terceros",
            "Costo Total Repuestos",
            "Costo Total General",
        ]
    )
    vehicles = Vehicle.objects.all()
    for vehicle in vehicles:
        costs = WorkOrder.objects.filter(
            vehicle=vehicle, status=WorkOrder.OrderStatus.VERIFIED
        ).aggregate(
            total_internal=Sum("labor_cost_internal"),
            total_external=Sum("labor_cost_external"),
            total_parts=Sum("parts_cost"),
        )
        cost_internal = costs["total_internal"] or 0
        cost_external = costs["total_external"] or 0
        cost_parts = costs["total_parts"] or 0
        total_general = cost_internal + cost_external + cost_parts
        writer.writerow(
            [
                vehicle.plate,
                vehicle.brand,
                vehicle.model,
                vehicle.year,
                cost_internal,
                cost_external,
                cost_parts,
                total_general,
            ]
        )
    return response


# --- NUEVO REPORTE ---
@user_passes_test(lambda u: u.is_superuser)
def preventive_compliance_report(request):
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="reporte_cumplimiento_preventivos_{timezone.now().strftime("%Y-%m-%d")}.csv"'
        },
    )
    response.write("\ufeff".encode("utf8"))
    writer = csv.writer(response)
    writer.writerow(
        [
            "Placa",
            "Zona Actual",
            "KM Actual",
            "Estado Odómetro",
            "Manual Asignado",
            "KM Último Preventivo",
            "Próximo Hito (KM)",
            "Descripción Próxima Tarea",
            "KM para Próximo Servicio",
            "Estado de Cumplimiento",
        ]
    )

    # Buscamos solo vehículos con planes de mantenimiento activos
    active_plans = MaintenancePlan.objects.filter(is_active=True).select_related(
        "vehicle", "manual"
    )

    for plan in active_plans:
        vehicle = plan.vehicle
        status = "A Tiempo"
        next_due_km = "N/A"
        next_task_desc = "N/A"
        km_remaining = "N/A"

        if plan.manual and vehicle.odometer_status == "VALID":
            km_since_last_service = vehicle.current_odometer_km - plan.last_service_km

            next_task = (
                plan.manual.tasks.filter(km_interval__gt=km_since_last_service)
                .order_by("km_interval")
                .first()
            )

            if next_task:
                next_due_km = plan.last_service_km + next_task.km_interval
                next_task_desc = next_task.description
                km_remaining = next_due_km - vehicle.current_odometer_km

                if vehicle.current_odometer_km >= next_due_km:
                    status = "VENCIDO"
                elif km_remaining <= 500:  # Umbral de advertencia
                    status = "Próximo a Vencer"
            else:
                status = "Completado (Sin más tareas)"
        elif vehicle.odometer_status == "INVALID":
            status = "Odómetro Inválido"

        writer.writerow(
            [
                vehicle.plate,
                vehicle.current_zone.name if vehicle.current_zone else "Sin Zona",
                vehicle.current_odometer_km,
                vehicle.get_odometer_status_display(),
                plan.manual.name if plan.manual else "Sin Manual",
                plan.last_service_km,
                next_due_km,
                next_task_desc,
                km_remaining,
                status,
            ]
        )

    return response
