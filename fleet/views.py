"""Viewsets for the fleet application."""

from rest_framework import viewsets
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing vehicles."""

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

# --- VISTAS HTML SIMPLES ---
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from workorders.models import WorkOrder


@staff_member_required
def vehicles_scheduled_view(request):
    """Lista de vehículos con OT programada en el futuro."""

    today = timezone.now()
    vehicles = (
        Vehicle.objects.filter(
            workorder__status=WorkOrder.OrderStatus.SCHEDULED,
            workorder__scheduled_start__isnull=False,
            workorder__scheduled_start__gt=today,
        )
        .order_by("plate")
        .distinct()
    )
    context = {"vehicles": vehicles, "title": "Vehículos con OT Programada"}
    return render(request, "fleet/vehicles_scheduled.html", context)


@staff_member_required
def vehicles_in_workshop_view(request):
    """Lista de vehículos actualmente en el taller."""

    today = timezone.now()
    vehicles = (
        Vehicle.objects.filter(
            workorder__check_in_at__isnull=False,
            workorder__check_in_at__lte=today,
        )
        .exclude(
            workorder__status__in=[
                WorkOrder.OrderStatus.SCHEDULED,
                WorkOrder.OrderStatus.COMPLETED,
                WorkOrder.OrderStatus.VERIFIED,
                WorkOrder.OrderStatus.CANCELLED,
            ]
        )
        .order_by("plate")
        .distinct()
    )
    context = {"vehicles": vehicles, "title": "Vehículos en Taller"}
    return render(request, "fleet/vehicles_in_workshop.html", context)


@staff_member_required
def vehicles_available_view(request):
    """Lista de vehículos sin órdenes de trabajo activas."""

    active_statuses = [
        WorkOrder.OrderStatus.SCHEDULED,
        WorkOrder.OrderStatus.IN_RECEPTION,
        WorkOrder.OrderStatus.IN_SERVICE,
        WorkOrder.OrderStatus.WAITING_PART,
        WorkOrder.OrderStatus.PENDING_APPROVAL,
        WorkOrder.OrderStatus.STOPPED_BY_CLIENT,
        WorkOrder.OrderStatus.IN_ROAD_TEST,
    ]

    vehicles = (
        Vehicle.objects.exclude(workorder__status__in=active_statuses)
        .order_by("plate")
        .distinct()
    )
    context = {"vehicles": vehicles, "title": "Vehículos Disponibles"}
    return render(request, "fleet/vehicles_available.html", context)
