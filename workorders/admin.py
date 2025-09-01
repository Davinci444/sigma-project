# workorders/admin.py
from django.contrib import admin
from django.shortcuts import redirect
from .models import WorkOrder, WorkOrderNote

# --- Admin de OT: redirige a la IU unificada ---
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle", "order_type", "status", "priority", "scheduled_start", "scheduled_end")
    search_fields = ("id",)
    list_filter = ("order_type", "status", "priority")

    # NO raw_id_fields => no "lupa" en admin (igual redirigimos)
    raw_id_fields = ()

    def add_view(self, request, form_url='', extra_context=None):
        return redirect("/api/workorders/workorders/new/")

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return redirect(f"/api/workorders/workorders/{object_id}/edit/")

# --- Novedades visibles en admin (opcional) ---
@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "author", "created_at")
    search_fields = ("work_order__id", "text")

# --- Ocultar modelos que no quieres tocar desde admin ---
def _try_unregister(model_label):
    try:
        from django.apps import apps
        m = apps.get_model(*model_label.split("."))
        admin.site.unregister(m)
    except Exception:
        pass

# Si existieran y estaban registrados:
for dotted in [
    "workorders.WorkOrderTask",
    "workorders.WorkOrderAttachment",
    "workorders.WorkOrderDriver",
    "workorders.WorkOrderPart",
    # agrega más si fuera necesario ocultarlos del admin
]:
    _try_unregister(dotted)
