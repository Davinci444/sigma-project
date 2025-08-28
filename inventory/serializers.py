"""Serializers for the inventory application."""

from rest_framework import serializers
from .models import Part, Supplier


class PartSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~inventory.models.Part`."""

    class Meta:
        model = Part
        fields = "__all__"


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~inventory.models.Supplier`."""

    class Meta:
        model = Supplier
        fields = "__all__"

