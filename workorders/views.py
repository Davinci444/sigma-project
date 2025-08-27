# workorders/views.py
from rest_framework import viewsets
from .models import WorkOrder, MaintenancePlan
from .serializers import WorkOrderSerializer, MaintenancePlanSerializer

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer