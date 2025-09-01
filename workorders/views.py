# workorders/views.py
"""Vista unificada para crear/editar OT con todo en la misma página."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from rest_framework import viewsets

from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
from .serializers import (
    WorkOrderSerializer, MaintenancePlanSerializer,
    WorkOrderTaskSerializer, WorkOrderPartSerializer
)
from .forms import (
    WorkOrderUnifiedForm, TaskFormSet, EvidenceURLFormSet, WorkOrderNoteForm
)

# ========= API existente (intacto) =========
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


# ========= VISTA UNIFICADA =========
@staff_member_required
def workorder_unified(request, pk=None):
    """
    - Si pk es None: crear OT
    - Si pk existe: editar OT
    Todo en una pantalla: datos base, conductor, (correctivo) prediagnóstico/origen/severidad,
    tareas (categoría/subcategoría), evidencias (URL) y novedades.
    """
    instance = get_object_or_404(WorkOrder, pk=pk) if pk else None

    if request.method == "POST":
        form = WorkOrderUnifiedForm(request.POST, instance=instance)
        if instance:
            task_fs = TaskFormSet(request.POST, instance=instance, prefix="tasks")
            evid_fs = EvidenceURLFormSet(request.POST, instance=instance, prefix="evid")
        else:
            # guardamos luego de crear para enlazar formsets
            task_fs = None
            evid_fs = None

        note_form = WorkOrderNoteForm(request.POST, prefix="note")

        if form.is_valid():
            ot = form.save(user=request.user)
            # Si era creación, ahora sí instanciamos formsets con la OT
            if task_fs is None:
                task_fs = TaskFormSet(request.POST, instance=ot, prefix="tasks")
                evid_fs = EvidenceURLFormSet(request.POST, instance=ot, prefix="evid")

            if task_fs.is_valid() and evid_fs.is_valid():
                task_fs.save()
                evid_fs.save()

                # Novedad (opcional)
                if note_form.is_valid() and note_form.cleaned_data.get("text"):
                    note = note_form.save(commit=False)
                    note.work_order = ot
                    note.author = request.user
                    note.save()

                # Recalcular costos si tu modelo lo hace
                if hasattr(ot, "recalculate_costs"):
                    ot.recalculate_costs()

                messages.success(request, f"OT #{ot.id} guardada correctamente.")
                return redirect("workorders_unified_edit", pk=ot.id)
            else:
                messages.error(request, "Corrige los errores en Tareas/Evidencias.")
                instance = ot  # para re-render
        else:
            messages.error(request, "Revisa los datos de la Orden de Trabajo.")
    else:
        form = WorkOrderUnifiedForm(instance=instance)
        task_fs = TaskFormSet(instance=instance, prefix="tasks") if instance else TaskFormSet(prefix="tasks")
        evid_fs = EvidenceURLFormSet(instance=instance, prefix="evid") if instance else EvidenceURLFormSet(prefix="evid")
        note_form = WorkOrderNoteForm(prefix="note")

    # Novedades existentes
    notes = instance.notes.order_by("-created_at") if instance and hasattr(instance, "notes") else []

    return render(request, "workorders/order_full_form.html", {
        "form": form,
        "task_fs": task_fs,
        "evid_fs": evid_fs,
        "note_form": note_form,
        "notes": notes,
        "ot": instance,
        "title": ("Editar OT" if instance else "Nueva OT"),
    })


# ========= REDIRECCIONES desde las rutas viejas =========
@require_http_methods(["GET", "POST"])
def new_preventive(request):
    return redirect("workorders_unified_new")

@require_http_methods(["GET", "POST"])
def new_corrective(request):
    return redirect("workorders_unified_new")

@require_http_methods(["GET", "POST"])
def edit_tasks(request, pk: int):
    return redirect("workorders_unified_edit", pk=pk)
