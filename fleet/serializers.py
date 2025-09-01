"""Serializers for the fleet application."""

from rest_framework import serializers
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~fleet.models.Vehicle`."""
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VehicleType.choices)

    class Meta:
        model = Vehicle
        fields = "__all__"  # Incluir todos los campos del modelo

