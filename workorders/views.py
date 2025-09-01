# workorders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from rest_framework import viewsets

from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
from .serializers import (
    WorkOrderSerializer, MaintenancePlanSerializer,
    WorkOrderTaskSerializer, WorkOrderPartSerializer
)
from .forms import (
    WorkOrderUnifiedForm, TaskFormSet, EvidenceURLFormSet, WorkOrderNoteForm
)

# ========= API (sin cambios de comportamiento) =========
class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().prefetch_related("tasks", "parts_used", "attachments", "notes")
    serializer_class = WorkOrderSerializer

class WorkOrderTaskViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderTask.objects.all()
    serializer_class = WorkOrderTaskSerializer

class WorkOrderPartViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderPart.objects.all()
    serializer_class = WorkOrderPartSerializer

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer


# ========= Vista unificada (única pantalla) =========
@staff_member_required
def workorder_unified(request, pk=None):
    ot = get_object_or_404(WorkOrder, pk=pk) if pk else None

    if request.method == "POST":
        form = WorkOrderUnifiedForm(request.POST, instance=ot)
        if ot:
            task_fs = TaskFormSet(request.POST, instance=ot, prefix="tasks")
            evid_fs = EvidenceURLFormSet(request.POST, instance=ot, prefix="evid")
        else:
            task_fs = None
            evid_fs = None

        note_form = WorkOrderNoteForm(request.POST, prefix="note")

        if form.is_valid():
            ot_saved = form.save(user=request.user)
            if task_fs is None:
                task_fs = TaskFormSet(request.POST, instance=ot_saved, prefix="tasks")
                evid_fs = EvidenceURLFormSet(request.POST, instance=ot_saved, prefix="evid")

            if task_fs.is_valid() and evid_fs.is_valid():
                task_fs.save()
                evid_fs.save()
                if note_form.is_valid() and note_form.cleaned_data.get("text"):
                    note = note_form.save(commit=False)
                    note.work_order = ot_saved
                    note.author = request.user
                    note.save()

                if hasattr(ot_saved, "recalculate_costs"):
                    ot_saved.recalculate_costs()

                messages.success(request, f"OT #{ot_saved.id} guardada correctamente.")
                return redirect("workorders_unified_edit", pk=ot_saved.id)
            else:
                messages.error(request, "Corrige los errores en Tareas/Evidencias.")
                ot = ot_saved  # re-render
        else:
            messages.error(request, "Revisa los datos de la Orden de Trabajo.")
    else:
        form = WorkOrderUnifiedForm(instance=ot)
        task_fs = TaskFormSet(instance=ot, prefix="tasks") if ot else TaskFormSet(prefix="tasks")
        evid_fs = EvidenceURLFormSet(instance=ot, prefix="evid") if ot else EvidenceURLFormSet(prefix="evid")
        note_form = WorkOrderNoteForm(prefix="note")

    notes = ot.notes.order_by("-created_at") if ot and hasattr(ot, "notes") else []

    # Pasamos la lista de campos datetime "reales" presentes para pintarlos
    datetime_real_fields = [f for f in WorkOrderUnifiedForm.dynamic_datetime_fields if f in form.fields]

    return render(request, "workorders/order_full_form.html", {
        "form": form,
        "task_fs": task_fs,
        "evid_fs": evid_fs,
        "note_form": note_form,
        "notes": notes,
        "ot": ot,
        "datetime_real_fields": datetime_real_fields,
        "title": ("Editar OT" if ot else "Nueva OT"),
    })


# ========= Compatibilidad/rutas viejas: redirigen aquí =========
@require_http_methods(["GET", "POST"])
def new_preventive(request):
    return redirect("workorders_unified_new")

@require_http_methods(["GET", "POST"])
def new_corrective(request):
    return redirect("workorders_unified_new")

@require_http_methods(["GET", "POST"])
def edit_tasks(request, pk: int):
    return redirect("workorders_unified_edit", pk=pk)
