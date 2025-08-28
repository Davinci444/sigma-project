"""Viewsets for work orders and related entities."""

from rest_framework import viewsets
from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
from .serializers import (
    WorkOrderSerializer,
    MaintenancePlanSerializer,
    WorkOrderTaskSerializer,
    WorkOrderPartSerializer,
)


class WorkOrderViewSet(viewsets.ModelViewSet):
    """API endpoint for work orders."""

    queryset = WorkOrder.objects.all().prefetch_related("tasks", "parts_used")
    serializer_class = WorkOrderSerializer


class MaintenancePlanViewSet(viewsets.ModelViewSet):
    """API endpoint for maintenance plans."""

    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer


# Nuevas vistas para gestionar tareas y repuestos de una OT
class WorkOrderTaskViewSet(viewsets.ModelViewSet):
    """API endpoint for work order tasks."""

    queryset = WorkOrderTask.objects.all()
    serializer_class = WorkOrderTaskSerializer


class WorkOrderPartViewSet(viewsets.ModelViewSet):
    """API endpoint for work order parts."""

    queryset = WorkOrderPart.objects.all()
    serializer_class = WorkOrderPartSerializer

# --- VISTA HTML DE PROGRAMACIÓN ---
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from collections import defaultdict

@staff_member_required
def schedule_view(request):
    """
    Muestra las OTs programadas agrupadas por fecha (scheduled_start.date).
    Solo estados programables.
    """
    from .models import WorkOrder
    qs = (WorkOrder.objects
          .filter(status__in=[
              WorkOrder.OrderStatus.SCHEDULED,
              WorkOrder.OrderStatus.IN_RECEPTION,
              WorkOrder.OrderStatus.IN_SERVICE,
              WorkOrder.OrderStatus.WAITING_PART,
              WorkOrder.OrderStatus.PENDING_APPROVAL,
              WorkOrder.OrderStatus.STOPPED_BY_CLIENT,
          ])
          .select_related("vehicle")
          .order_by("scheduled_start", "priority", "id"))

    grouped = defaultdict(list)
    for ot in qs:
        day = (ot.scheduled_start.date() if ot.scheduled_start else timezone.now().date())
        grouped[day].append(ot)

    ordered_days = sorted(grouped.keys())
    return render(request, "workorders/schedule.html", {
        "days": ordered_days,
        "grouped": grouped,
        "title": "Programación de Vehículos por Fecha",
    })
