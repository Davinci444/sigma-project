# workorders/views.py
from rest_framework import viewsets
from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
from .serializers import (
    WorkOrderSerializer, 
    MaintenancePlanSerializer, 
    WorkOrderTaskSerializer, 
    WorkOrderPartSerializer
)

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().prefetch_related('tasks', 'parts_used')
    serializer_class = WorkOrderSerializer

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer

# Nuevas vistas para gestionar tareas y repuestos de una OT
class WorkOrderTaskViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderTask.objects.all()
    serializer_class = WorkOrderTaskSerializer

class WorkOrderPartViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderPart.objects.all()
    serializer_class = WorkOrderPartSerializer