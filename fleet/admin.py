"""Admin configuration for the fleet application."""

from django.contrib import admin
from .models import Vehicle, VehicleZoneHistory


class VehicleOperationalStatusFilter(admin.SimpleListFilter):
    """Filter vehicles by operational status."""

    title = "Estado Operativo"  # El título que verás en el panel de filtros
    parameter_name = "operational_status"  # El nombre que se usará en la URL

    def lookups(self, request, model_admin):
        """Return available filter options."""

        return (("in_repair", "En Taller (Reparación)"),)

    def queryset(self, request, queryset):
        """Filter queryset based on the selected option."""

        if self.value() == "in_repair":
            return queryset.filter(status=Vehicle.VehicleStatus.IN_REPAIR)
        return queryset


class VehicleZoneHistoryInline(admin.TabularInline):
    """Inline history of zones for a vehicle."""

    model = VehicleZoneHistory
    extra = 0
    readonly_fields = ("start_date", "end_date")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin interface for :class:`~fleet.models.Vehicle`."""

    list_display = (
        "plate",
        "brand",
        "model",
        "current_zone",
        "status",
        "current_odometer_km",
    )
    search_fields = ("plate", "vin", "brand", "model")
    list_filter = (
        VehicleOperationalStatusFilter,
        "status",
        "current_zone",
        "fuel_type",
    )
    readonly_fields = ("current_odometer_km",)
    fieldsets = (
        (None, {"fields": ("plate", "vin", "brand", "model", "year", "vehicle_type", "fuel_type", "status")} ),
        ("Operación y Estado", {"fields": ("current_zone", "current_odometer_km", "odometer_status")} ),
        ("Documentación", {"fields": ("soat_due_date", "rtm_due_date")} ),
    )
    inlines = [VehicleZoneHistoryInline]

    def get_queryset(self, request):
        """Restrict visible vehicles based on user zone."""

        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            try:
                user_zone = request.user.profile.zone
                if user_zone:
                    return qs.filter(current_zone=user_zone)
            except AttributeError:
                return qs.none()
        return qs

