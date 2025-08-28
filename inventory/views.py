# inventory/views.py
from rest_framework import viewsets
from .models import Part, Supplier
from .serializers import PartSerializer, SupplierSerializer


class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
