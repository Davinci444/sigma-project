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

