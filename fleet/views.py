"""Viewsets for the fleet application."""

from rest_framework import viewsets
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing vehicles."""

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

