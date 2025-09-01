"""Serializers for the fleet application."""

from rest_framework import serializers
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for :class:`~fleet.models.Vehicle`."""

    def validate_vehicle_type(self, value: str) -> str:
        """Ensure ``vehicle_type`` matches the allowed choices.

        Django's ``ChoiceField`` normally validates input, but we add an
        explicit check to provide a clearer error message and guard against
        unexpected values that could bubble up as 500 errors.
        """
        allowed = {
            choice[0]
            for choice in Vehicle._meta.get_field("vehicle_type").choices
        }
        if value not in allowed:
            allowed_display = ", ".join(sorted(allowed))
            raise serializers.ValidationError(
                f"Invalid vehicle_type '{value}'. Allowed values are: {allowed_display}."
            )
        return value

    class Meta:
        model = Vehicle
        fields = "__all__"  # Incluir todos los campos del modelo

