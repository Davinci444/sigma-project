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
        return redirect(reverse("workorders_unified_new"))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return redirect(reverse("workorders_unified_edit", args=[object_id]))

@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "author", "created_at") if hasattr(WorkOrderNote, "author") else ("id","work_order","created_at")
    search_fields = ("work_order__id", "text")
    list_select_related = ("work_order", "author") if hasattr(WorkOrderNote, "author") else ("work_order",)
