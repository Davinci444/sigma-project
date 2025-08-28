"""Viewsets for the inventory application."""

from rest_framework import viewsets
from .models import Part, Supplier
from .serializers import PartSerializer, SupplierSerializer


class PartViewSet(viewsets.ModelViewSet):
    """API endpoint for parts."""

    queryset = Part.objects.all()
    serializer_class = PartSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    """API endpoint for suppliers."""

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

