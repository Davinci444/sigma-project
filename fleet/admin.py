"""Admin de Vehículos con columnas útiles y seguras (sin suposiciones de campos)."""

from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Lista de vehículos con:
    - Placa
    - Usuario/Gestor asignado (si existe algún campo razonable)
    - Odómetro, tipo de vehículo y tipo de combustible
    """

    list_display = (
        "plate",
        "usuario_gestor_asignado",
        "current_odometer_km",
        "vehicle_type",
        "fuel_type",
    )
    list_filter = (
        "vehicle_type",
        "fuel_type",
    )
    search_fields = (
        "plate",
        "vin",
        "brand",
        "model",
    )
    ordering = ("plate",)

    def usuario_gestor_asignado(self, obj: Vehicle):
        """
        Intenta mostrar un “usuario/gestor” asociado al vehículo.
        No asumimos nombres de campo. Probamos varios comunes.
        Si no existe, devolvemos “—” (no rompe).
        """
        candidates = [
            "assigned_user",
            "user",
            "owner",
            "manager",
            "assigned_to",
        ]
        for name in candidates:
            if hasattr(obj, name):
                u = getattr(obj, name)
                if u:
                    full = getattr(u, "get_full_name", lambda: "")() or ""
                    label = full or getattr(u, "username", None) or str(u)
                    return label
        return "—"

    usuario_gestor_asignado.short_description = "Usuario / Gestor"
