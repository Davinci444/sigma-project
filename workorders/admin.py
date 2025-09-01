# workorders/admin.py
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import (
    MaintenanceManual,
    MaintenancePlan,
    WorkOrder,
    WorkOrderNote,
)

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle", "order_type", "status", "priority", "scheduled_start", "scheduled_end")
    search_fields = ("id", "vehicle__plate", "vehicle__vin")
    list_filter = ("order_type", "status", "priority")
    raw_id_fields = ()  # sin lupas

    def add_view(self, request, form_url='', extra_context=None):
        return redirect(reverse("workorders_admin_new"))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return redirect(reverse("workorders_admin_edit", args=[object_id]))

@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "author", "created_at") if hasattr(WorkOrderNote, "author") else ("id","work_order","created_at")
    search_fields = ("work_order__id", "text")
    list_select_related = ("work_order", "author") if hasattr(WorkOrderNote, "author") else ("work_order",)


# --- Registro de Manuales y Planes de Mantenimiento ---


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "fuel_type")
    search_fields = ("name",)
    list_filter = ("fuel_type",)


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vehicle",
        "manual",
        "last_service_km",
        "last_service_date",
        "is_active",
    )
    search_fields = (
        "vehicle__plate",
        "vehicle__vin",
        "manual__name",
    )
    list_filter = ("manual", "is_active")
    list_select_related = ("vehicle", "manual")
