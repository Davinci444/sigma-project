"""Admin mínimo y robusto para evitar 500 en 'Agregar OT'.
   Nota: dejamos fuera inlines y dependencias. Luego los reactivamos paso a paso.
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
# Planes (sin autocomplete dependiente)
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
# Órdenes de trabajo (ULTRA MINIMAL)
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

    # Campos mínimos y seguros que existen en tu modelo
    fields = (
        "order_type", "status", "vehicle", "priority",
        "description", "scheduled_start", "scheduled_end",
        "check_in_at", "check_out_at",
    )

# -------------------------
# (Opcional) Editores separados si los usas directo
# -------------------------

@admin.register(WorkOrderTask)
class WorkOrderTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "category", "subcategory", "is_completed")
    list_filter = ("is_completed", "category")
    search_fields = ("work_order__id", "work_order__vehicle__plate", "description")
    autocomplete_fields = ("work_order", "category", "subcategory")
    list_select_related = ("work_order", "category", "subcategory")


@admin.register(WorkOrderPart)
class WorkOrderPartAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "part", "quantity", "unit_cost")
    search_fields = ("work_order__id", "work_order__vehicle__plate", "part__name")
    autocomplete_fields = ("work_order", "part")
    list_select_related = ("work_order", "part")
