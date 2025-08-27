# workorders/serializers.py
from rest_framework import serializers
from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart

class WorkOrderTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderTask
        fields = '__all__'

class WorkOrderPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderPart
        fields = '__all__'

class WorkOrderSerializer(serializers.ModelSerializer):
    # Hacemos que las tareas y repuestos se puedan ver al consultar una OT
    tasks = WorkOrderTaskSerializer(many=True, read_only=True)
    parts_used = WorkOrderPartSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = '__all__'

class MaintenancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePlan
        fields = '__all__'