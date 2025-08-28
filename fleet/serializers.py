"""Serializers for the fleet application."""

from rest_framework import serializers
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~fleet.models.Vehicle`."""

    class Meta:
        model = Vehicle
        fields = "__all__"  # Incluir todos los campos del modelo

