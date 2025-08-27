# reports/views.py
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.db.models import Sum, F

from fleet.models import Vehicle
from workorders.models import WorkOrder

# Solo los superusuarios pueden descargar reportes
@user_passes_test(lambda u: u.is_superuser)
def vehicle_costs_report(request):
    # 1. Preparamos el archivo de respuesta
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="reporte_costos_vehiculos_{timezone.now().strftime("%Y-%m-%d")}.csv"'},
    )
    response.write(u'\ufeff'.encode('utf8')) # Para asegurar compatibilidad con caracteres en español

    # 2. Creamos el escritor de CSV
    writer = csv.writer(response)
    writer.writerow(['Placa', 'Marca', 'Modelo', 'Año', 'Costo Total MO Interna', 'Costo Total MO Terceros', 'Costo Total Repuestos', 'Costo Total General'])

    # 3. Consultamos y agregamos los datos
    # Obtenemos todos los vehículos
    vehicles = Vehicle.objects.all()

    for vehicle in vehicles:
        # Para cada vehículo, sumamos los costos de todas sus OTs cerradas
        costs = WorkOrder.objects.filter(
            vehicle=vehicle,
            status=WorkOrder.OrderStatus.VERIFIED
        ).aggregate(
            total_internal=Sum('labor_cost_internal'),
            total_external=Sum('labor_cost_external'),
            total_parts=Sum('parts_cost')
        )

        cost_internal = costs['total_internal'] or 0
        cost_external = costs['total_external'] or 0
        cost_parts = costs['total_parts'] or 0
        total_general = cost_internal + cost_external + cost_parts

        writer.writerow([
            vehicle.plate,
            vehicle.brand,
            vehicle.model,
            vehicle.year,
            cost_internal,
            cost_external,
            cost_parts,
            total_general
        ])

    return response