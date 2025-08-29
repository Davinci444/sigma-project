"""Admin ultra estable para evitar 500 en 'Agregar OT'.
   - Sin inlines en WorkOrder (por ahora).
   - Sin menús independientes de Tareas/Repuestos (los reactivamos más adelante, dentro de cada OT).
   - Añade proxies: Órdenes Preventivas / Órdenes Correctivas (formularios mínimos).
"""

from django.contrib import admin
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
from .proxies import PreventiveOrder, CorrectiveOrder


# -------------------------
# Catálogos / Manuales
# -------------------------

@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(MaintenanceSubcategory)
class MaintenanceSubcategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    list_filter = ("category",)
    search_fields = ("name", "category__name")
    autocomplete_fields = ("category",)


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "fuel_type")
    list_filter = ("fuel_type",)
    search_fields = ("name",)


@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "manual", "description", "km_interval")
    list_filter = ("manual",)
    search_fields = ("description", "manual__name")
    autocomplete_fields = ("manual",)


# -------------------------
# Planes (robusto en Add)
# -------------------------

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle", "manual", "is_active", "last_service_km", "last_service_date")
    list_filter = ("is_active", "manual")
    search_fields = ("vehicle__plate", "manual__name")
    raw_id_fields = ("vehicle", "manual")
    list_select_related = ("vehicle", "manual")
    date_hierarchy = "last_service_date"


# -------------------------
# Órdenes de trabajo (ULTRA MINIMAL, sin inlines)
# -------------------------

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """Admin básico para garantizar que '/add/' nunca falle."""
    list_display = ("id", "order_type", "status", "vehicle", "scheduled_start")
    list_filter = ("order_type", "status")
    search_fields = ("id", "vehicle__plate")
    raw_id_fields = ("vehicle",)
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    fields = (
        "order_type",
        "status",
        "vehicle",
        "priority",
        "description",
        "scheduled_start",
        "scheduled_end",
        "check_in_at",
        "check_out_at",
    )

# IMPORTANTE:
# - NO registramos WorkOrderTask ni WorkOrderPart como menús (se verán como inlines más adelante).


# -------------------------
# PROXIES: Preventiva / Correctiva (formularios mínimos, sin inlines)
# -------------------------

@admin.register(PreventiveOrder)
class PreventiveOrderAdmin(admin.ModelAdmin):
    """Vista dedicada para Preventivas: fija el tipo al guardar y filtra el listado."""
    list_display = ("id", "status", "vehicle", "scheduled_start")
    list_filter = ("status",)
    search_fields = ("id", "vehicle__plate")
    raw_id_fields = ("vehicle",)
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    # No mostramos order_type aquí; lo fijamos al guardar.
    fields = (
        "status",
        "vehicle",
        "priority",
        "description",
        "scheduled_start",
        "scheduled_end",
        "check_in_at",
        "check_out_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(order_type=WorkOrder.OrderType.PREVENTIVE)

    def save_model(self, request, obj, form, change):
        obj.order_type = WorkOrder.OrderType.PREVENTIVE
        super().save_model(request, obj, form, change)


@admin.register(CorrectiveOrder)
class CorrectiveOrderAdmin(admin.ModelAdmin):
    """Vista dedicada para Correctivas: fija el tipo al guardar y filtra el listado."""
    list_display = ("id", "status", "vehicle", "scheduled_start")
    list_filter = ("status",)
    search_fields = ("id", "vehicle__plate")
    raw_id_fields = ("vehicle",)
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    fields = (
        "status",
        "vehicle",
        "priority",
        "description",
        "scheduled_start",
        "scheduled_end",
        "check_in_at",
        "check_out_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(order_type=WorkOrder.OrderType.CORRECTIVE)

    def save_model(self, request, obj, form, change):
        obj.order_type = WorkOrder.OrderType.CORRECTIVE
        super().save_model(request, obj, form, change)
