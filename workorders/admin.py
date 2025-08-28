"""Admin configuration for work order management."""

from datetime import timedelta

from django.contrib import admin, messages
from django.utils import timezone

from .models import (
    MaintenancePlan,
    WorkOrder,
    WorkOrderTask,
    WorkOrderPart,
    MaintenanceCategory,
    MaintenanceSubcategory,
    MaintenanceManual,
    ManualTask,
)


class OperationalStatusFilter(admin.SimpleListFilter):
    """Filter work orders by the operational status of their vehicles."""

    title = "Estado Operativo"
    parameter_name = "operational_status"

    def lookups(self, request, model_admin):
        """Return available filter options."""

        return (
            ("in_workshop", "Vehículos en Taller"),
            ("scheduled", "Vehículos Programados"),
        )

    def queryset(self, request, queryset):
        """Filter the queryset according to the selected option."""

        today = timezone.now()
        if self.value() == "in_workshop":
            return queryset.filter(
                check_in_at__isnull=False,
                check_in_at__lte=today,
            ).exclude(
                status__in=[WorkOrder.OrderStatus.VERIFIED, WorkOrder.OrderStatus.CANCELLED]
            )
        if self.value() == "scheduled":
            return queryset.filter(
                status=WorkOrder.OrderStatus.SCHEDULED,
                scheduled_start__isnull=False,
                scheduled_start__gt=today,
            )
        return queryset


class MaintenanceSubcategoryInline(admin.TabularInline):
    """Inline display of maintenance subcategories."""

    model = MaintenanceSubcategory
    extra = 1


@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    """Admin interface for maintenance categories."""

    list_display = ("name", "description")
    search_fields = ("name",)
    inlines = [MaintenanceSubcategoryInline]


class ManualTaskInline(admin.TabularInline):
    """Inline display of manual tasks."""

    model = ManualTask
    extra = 1


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    """Admin interface for maintenance manuals."""

    list_display = ("name", "fuel_type")
    inlines = [ManualTaskInline]


class WorkOrderTaskInline(admin.TabularInline):
    """Inline tasks within a work order."""

    model = WorkOrderTask
    extra = 1
    fields = (
        "category",
        "subcategory",
        "description",
        "hours_spent",
        "is_external",
        "labor_rate",
    )


class WorkOrderPartInline(admin.TabularInline):
    """Inline parts used in a work order."""

    model = WorkOrderPart
    extra = 1


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    """Admin interface for maintenance plans."""

    list_display = (
        "vehicle",
        "manual",
        "is_active",
        "last_service_km",
        "last_service_date",
    )
    list_filter = ("is_active", "manual")
    readonly_fields = ("is_active", "last_service_km", "last_service_date")


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """Admin interface for work orders."""

    list_display = (
        "id",
        "order_type",
        "vehicle",
        "status",
        "priority",
        "scheduled_start",
    )
    search_fields = ("id", "vehicle__plate", "description")
    list_filter = (OperationalStatusFilter, "status", "priority", "order_type")
    inlines = [WorkOrderTaskInline, WorkOrderPartInline]
    fieldsets = (
        (
            "Información Principal",
            {
                "fields": (
                    "order_type",
                    "vehicle",
                    "status",
                    "priority",
                    "assigned_technician",
                    "odometer_at_service",
                )
            },
        ),
        ("Descripción del Trabajo", {"fields": ("description",)}),
        (
            "Programación y Tiempos",
            {
                "fields": (
                    "scheduled_start",
                    "scheduled_end",
                    "check_in_at",
                    "check_out_at",
                )
            },
        ),
        (
            "Costos (Calculados)",
            {
                "fields": ("labor_cost_internal", "labor_cost_external", "parts_cost"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("labor_cost_internal", "labor_cost_external", "parts_cost")

    def get_queryset(self, request):
        """Limit work orders to the user's zone when not a superuser."""

        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            try:
                user_zone = request.user.profile.zone
                if user_zone:
                    return qs.filter(vehicle__current_zone=user_zone)
            except (AttributeError, request.user.profile.DoesNotExist):
                return qs.none()
        return qs

    def save_model(self, request, obj, form, change):
        """Update maintenance plan when verifying preventive work orders."""

        super().save_model(request, obj, form, change)
        if (
            obj.order_type == WorkOrder.OrderType.PREVENTIVE
            and obj.status == WorkOrder.OrderStatus.VERIFIED
        ):
            plan = MaintenancePlan.objects.filter(vehicle=obj.vehicle).first()
            if plan and obj.odometer_at_service:
                if not plan.is_active:
                    plan.is_active = True
                plan.last_service_km = obj.odometer_at_service
                plan.last_service_date = (
                    obj.check_out_at.date() if obj.check_out_at else timezone.now().date()
                )
                plan.save()
                messages.success(
                    request,
                    f"Plan de mantenimiento para {obj.vehicle.plate} ha sido activado/actualizado.",
                )

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """Warn about overdue preventive maintenance when editing."""

        if obj and obj.vehicle:
            vehicle = obj.vehicle
            plan = MaintenancePlan.objects.filter(vehicle=vehicle, is_active=True).first()
            if plan and plan.manual and vehicle.odometer_status == "VALID":
                km_since_last_service = vehicle.current_odometer_km - plan.last_service_km
                next_task = (
                    plan.manual.tasks.filter(km_interval__gt=km_since_last_service)
                    .order_by("km_interval")
                    .first()
                )
                if not next_task:
                    next_task = plan.manual.tasks.order_by("-km_interval").first()
                if next_task:
                    next_due_km = plan.last_service_km + next_task.km_interval
                    if vehicle.current_odometer_km >= next_due_km:
                        mensaje = (
                            "¡Mantenimiento Preventivo VENCIDO! "
                            f"Próximo servicio ({next_task.description}) era a los {next_due_km} km."
                        )
                        messages.warning(request, f"ATENCIÓN: {mensaje}")
        return super().render_change_form(request, context, add, change, form_url, obj)

