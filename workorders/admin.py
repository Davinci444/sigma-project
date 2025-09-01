# workorders/admin.py
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from .models import WorkOrder, WorkOrderNote

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


# --- Registro de Manuales de Mantenimiento (solo lectura) ---
from django.utils.html import format_html

try:
    from .models import MaintenancePlan
except Exception:
    MaintenancePlan = None

if MaintenancePlan:
    @admin.register(MaintenancePlan)
    class MaintenancePlanAdmin(admin.ModelAdmin):
        # Ajusta columnas según tus campos reales:
        list_display = (
            "id",
            "name",                   # nombre del manual/plan
            "fuel_type",              # GASOLINA / DIESEL (si existe)
            "vehicle_type",           # opcional: tipo de vehículo (si existe)
            "interval_km",            # km entre servicios (si existe)
            "interval_days",          # días entre servicios (si existe)
            "is_active",              # activo/inactivo (si existe)
        )
        search_fields = ("name",)
        list_filter = ("fuel_type", "is_active")  # quita/añade según tus campos
        ordering = ("name",)

        # Para no romper nada, lo dejo editable por defecto.
        # Si quieres que sea solo lectura, descomenta esto:
        # def has_change_permission(self, request, obj=None):
        #     return False
        # def has_add_permission(self, request):
        #     return False
        # def has_delete_permission(self, request, obj=None):
        #     return False
