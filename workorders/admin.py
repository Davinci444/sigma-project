"""Admin mínimo y limpio para OT: sin menús extra de Tareas/Repuestos.
   (Se mantienen como inlines cuando edites una OT).
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
# Órdenes de trabajo (ULTRA MINIMAL y sin menús extra)
# -------------------------

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1
    autocomplete_fields = ("category", "subcategory")
    fields = ("category", "subcategory", "description", "estimated_hours", "actual_hours", "is_completed")


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1
    autocomplete_fields = ("part",)
    fields = ("part", "quantity", "unit_cost")


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """Admin básico para garantizar que '/add/' nunca falle y sin menús sobrantes."""
    list_display = ("id", "order_type", "status", "vehicle", "scheduled_start")
    list_filter = ("order_type", "status")
    search_fields = ("id", "vehicle__plate")
    raw_id_fields = ("vehicle",)
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)
    fields = (
        "order_type", "status", "vehicle", "priority",
        "description", "scheduled_start", "scheduled_end",
        "check_in_at", "check_out_at",
    )
    inlines = [WorkOrderTaskInline, WorkOrderPartInline]

# NOTA IMPORTANTE:
# - No registramos @admin.register(WorkOrderTask) ni @admin.register(WorkOrderPart)
#   para que NO aparezcan como menús independientes.
#   Se editan sólo dentro de la OT.
