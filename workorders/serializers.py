# workorders/serializers.py
from rest_framework import serializers
from .models import WorkOrder, MaintenancePlan

class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'

class MaintenancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePlan
        fields = '__all__'