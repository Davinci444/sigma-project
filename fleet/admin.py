"""Admin de Vehículos: columnas claras y filtros útiles sin depender de campos inexistentes."""

from django.contrib import admin
from django.db.models import Q
from .models import Vehicle
from workorders.models import WorkOrder


class EnTallerFilter(admin.SimpleListFilter):
    title = "¿Vehículo en taller?"
    parameter_name = "in_workshop"

    def lookups(self, request, model_admin):
        return (("yes", "Sí"), ("no", "No"))

    def queryset(self, request, qs):
        if self.value() == "yes":
            return qs.filter(
                workorder__check_in_at__isnull=False
            ).exclude(
                workorder__status__in=[
                    WorkOrder.OrderStatus.VERIFIED,
                    WorkOrder.OrderStatus.CANCELLED,
                    WorkOrder.OrderStatus.COMPLETED,
                ]
            ).distinct()
        if self.value() == "no":
            return qs.exclude(
                Q(workorder__check_in_at__isnull=False)
                & ~Q(workorder__status__in=[
                    WorkOrder.OrderStatus.VERIFIED,
                    WorkOrder.OrderStatus.CANCELLED,
                    WorkOrder.OrderStatus.COMPLETED,
                ])
            ).distinct()
        return qs


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate",
        "usuario_gestor_asignado",
        "current_odometer_km",
        "vehicle_type",
        "fuel_type",
        "en_taller",
    )
    list_filter = (
        "vehicle_type",
        "fuel_type",
        EnTallerFilter,
    )
    search_fields = ("plate", "vin", "brand", "model")
    ordering = ("plate",)

    def usuario_gestor_asignado(self, obj: Vehicle):
        """
        Muestra un “usuario/gestor” si tu modelo tiene alguno de estos campos.
        Si no existe, devuelve —.
        """
        for name in ("assigned_user", "user", "owner", "manager", "assigned_to"):
            if hasattr(obj, name):
                u = getattr(obj, name)
                if u:
                    full = getattr(u, "get_full_name", lambda: "")() or ""
                    return full or getattr(u, "username", None) or str(u)
        return "—"
    usuario_gestor_asignado.short_description = "Usuario / Gestor"

    def en_taller(self, obj: Vehicle) -> bool:
        return WorkOrder.objects.filter(
            vehicle=obj,
            check_in_at__isnull=False
        ).exclude(
            status__in=[
                WorkOrder.OrderStatus.VERIFIED,
                WorkOrder.OrderStatus.CANCELLED,
                WorkOrder.OrderStatus.COMPLETED,
            ]
        ).exists()
    en_taller.boolean = True
    en_taller.short_description = "En taller"
