# workorders/admin.py
from django.contrib import admin
from .models import (
    WorkOrder,
    WorkOrderNote,
    MaintenanceManual,
    ManualTask,
    WorkOrderTask,
)

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vehicle",
        "order_type",
        "status",
        "priority",
        "scheduled_start",
        "scheduled_end",
    )
    search_fields = ("id", "vehicle__plate", "vehicle__vin")
    list_filter = ("order_type", "status", "priority")
    raw_id_fields = ()  # sin lupas
    inlines = [WorkOrderTaskInline]

@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "author", "created_at") if hasattr(WorkOrderNote, "author") else ("id","work_order","created_at")
    search_fields = ("work_order__id", "text")
    list_select_related = ("work_order", "author") if hasattr(WorkOrderNote, "author") else ("work_order",)


# --- Registro de Manuales de Mantenimiento ---


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("name", "fuel_type")
    search_fields = ("name",)
    list_filter = ("fuel_type",)


@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    list_display = ("manual", "km_interval", "description")
    search_fields = ("manual__name", "description")
    list_filter = ("manual",)


# --- Registro de Planes de Mantenimiento (solo lectura) ---
from django.utils.html import format_html

try:
    from .models import MaintenancePlan
except Exception:
    MaintenancePlan = None

if MaintenancePlan:
    @admin.register(MaintenancePlan)
    class MaintenancePlanAdmin(admin.ModelAdmin):
        list_display = ("id", "vehicle", "manual", "is_active")
        search_fields = ("vehicle__plate",)
        list_filter = ("is_active",)
        ordering = ("id",)

        # Para no romper nada, lo dejo editable por defecto.
        # Si quieres que sea solo lectura, descomenta esto:
        # def has_change_permission(self, request, obj=None):
        #     return False
        # def has_add_permission(self, request):
        #     return False
        # def has_delete_permission(self, request, obj=None):
        #     return False
