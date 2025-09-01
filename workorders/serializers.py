"""Serializers for work order related models."""

from rest_framework import serializers
from .models import (
    WorkOrder,
    MaintenancePlan,
    WorkOrderTask,
    WorkOrderPart,
    MaintenanceCategory,
    MaintenanceSubcategory,
)


class WorkOrderTaskSerializer(serializers.ModelSerializer):
    """Serializer for work order tasks."""

    class Meta:
        model = WorkOrderTask
        fields = "__all__"


class WorkOrderPartSerializer(serializers.ModelSerializer):
    """Serializer for parts used in a work order."""

    class Meta:
        model = WorkOrderPart
        fields = "__all__"


class WorkOrderSerializer(serializers.ModelSerializer):
    """Serializer for work orders including nested tasks and parts."""

    tasks = WorkOrderTaskSerializer(many=True, read_only=True)
    parts_used = WorkOrderPartSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = "__all__"


class MaintenancePlanSerializer(serializers.ModelSerializer):
    """Serializer for maintenance plans."""

    class Meta:
        model = MaintenancePlan
        fields = "__all__"


class MaintenanceCategorySerializer(serializers.ModelSerializer):
    """Serializer for maintenance categories."""

    class Meta:
        model = MaintenanceCategory
        fields = "__all__"


class MaintenanceSubcategorySerializer(serializers.ModelSerializer):
    """Serializer for maintenance subcategories."""

    class Meta:
        model = MaintenanceSubcategory
        fields = "__all__"

