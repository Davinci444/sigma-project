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
    # Sin “lupas” (raw_id_fields vacío); de todas formas, el admin NO edita ni crea aquí.
    raw_id_fields = ()

    def add_view(self, request, form_url='', extra_context=None):
        # Siempre crear desde la IU unificada
        return redirect(reverse("workorders_unified_new"))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Siempre editar desde la IU unificada
        return redirect(reverse("workorders_unified_edit", args=[object_id]))

@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "author", "created_at")
    search_fields = ("work_order__id", "text")
    list_select_related = ("work_order", "author")
