"""Viewsets for the fleet application."""

from rest_framework import viewsets
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing vehicles."""

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

# --- VISTAS HTML SIMPLES ---
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def vehicles_in_repair_view(request):
    """Lista de vehículos con estado 'IN_REPAIR'."""
    from .models import Vehicle
    vehicles = Vehicle.objects.filter(status="IN_REPAIR").order_by("plate")
    return render(request, "fleet/vehicles_in_repair.html", {"vehicles": vehicles, "title": "Vehículos en Taller"})
