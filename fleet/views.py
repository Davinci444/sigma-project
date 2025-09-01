"""Viewsets for the fleet application."""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    """API endpoint for viewing and editing vehicles."""

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def _handle_request(self, request, partial=False, instance=None):
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        ) if instance else self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer) if not instance else self.perform_update(serializer)
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"detail": "Invalid vehicle data."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        headers = self.get_success_headers(serializer.data) if not instance else {}
        status_code = status.HTTP_201_CREATED if not instance else status.HTTP_200_OK
        return Response(serializer.data, status=status_code, headers=headers)

    def create(self, request, *args, **kwargs):
        return self._handle_request(request)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        return self._handle_request(request, partial=partial, instance=instance)

# --- VISTAS HTML SIMPLES ---
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def vehicles_in_repair_view(request):
    """Lista de vehículos con estado 'IN_REPAIR'."""
    from .models import Vehicle
    vehicles = Vehicle.objects.filter(status="IN_REPAIR").order_by("plate")
    return render(request, "fleet/vehicles_in_repair.html", {"vehicles": vehicles, "title": "Vehículos en Taller"})
