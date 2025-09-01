# workorders/views.py
"""Vistas HTML y API para órdenes de trabajo."""

from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from rest_framework import viewsets

from .models import (
    WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
)
from .serializers import (
    WorkOrderSerializer, MaintenancePlanSerializer,
    WorkOrderTaskSerializer, WorkOrderPartSerializer
)
from .forms import (
    WorkOrderPreventiveForm, WorkOrderCorrectiveForm,
    TaskFormSet, EvidenceURLFormSet
)


# =======================
# API (se mantiene)
# =======================
class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().prefetch_related("tasks", "parts_used")
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


# =======================
# HTML: Programación
# =======================
def schedule_view(request):
    """
    Muestra las OTs programadas agrupadas por fecha (scheduled_start.date).
    Solo estados programables.
    """
    qs = (WorkOrder.objects
          .filter(status__in=[
              WorkOrder.OrderStatus.SCHEDULED,
              WorkOrder.OrderStatus.IN_RECEPTION,
              WorkOrder.OrderStatus.IN_SERVICE,
              WorkOrder.OrderStatus.WAITING_PART,
              WorkOrder.OrderStatus.PENDING_APPROVAL,
              WorkOrder.OrderStatus.STOPPED_BY_CLIENT,
          ])
          .select_related("vehicle")
          .order_by("scheduled_start", "priority", "id")
    )

    grouped = defaultdict(list)
    for ot in qs:
        day = (ot.scheduled_start.date() if ot.scheduled_start else timezone.now().date())
        grouped[day].append(ot)

    ordered_days = sorted(grouped.keys())
    return render(request, "workorders/schedule.html", {
        "days": ordered_days,
        "grouped": grouped,
        "title": "Programación de Vehículos por Fecha",
    })


# =======================
# HTML: Crear OT
# =======================
def new_preventive(request):
    """Crear una OT PREVENTIVA (conductor + comentario inicial opcional)."""
    if request.method == "POST":
        form = WorkOrderPreventiveForm(request.POST)
        if form.is_valid():
            ot = form.save(user=request.user)
            messages.success(request, f"OT Preventiva #{ot.id} creada correctamente.")
            return redirect("workorders_edit_tasks", pk=ot.id)
        messages.error(request, "Revisa el formulario.")
    else:
        form = WorkOrderPreventiveForm()
    return render(request, "workorders/order_form.html", {
        "form": form, "title": "Nueva OT Preventiva"
    })

def new_corrective(request):
    """Crear una OT CORRECTIVA (pre-diagnóstico, severidad, origen, conductor)."""
    if request.method == "POST":
        form = WorkOrderCorrectiveForm(request.POST)
        if form.is_valid():
            ot = form.save(user=request.user)
            messages.success(request, f"OT Correctiva #{ot.id} creada correctamente.")
            return redirect("workorders_edit_tasks", pk=ot.id)
        messages.error(request, "Revisa el formulario.")
    else:
        form = WorkOrderCorrectiveForm()
    return render(request, "workorders/order_form.html", {
        "form": form, "title": "Nueva OT Correctiva"
    })


# =======================
# HTML: Agregar/Editar Tareas
# =======================
def edit_tasks(request, pk: int):
    """Agregar y editar trabajos (tareas) de una OT, más evidencias por URL."""
    ot = get_object_or_404(WorkOrder, pk=pk)
    if request.method == "POST":
        formset = TaskFormSet(request.POST, instance=ot, prefix="tasks")
        evidset = EvidenceURLFormSet(request.POST, instance=ot, prefix="evid")
        if formset.is_valid() and evidset.is_valid():
            formset.save()
            evidset.save()
            # recálculo de costos vía signals o manual
            ot.recalculate_costs()
            messages.success(request, "Tareas/Evidencias actualizadas.")
            return redirect("workorders_edit_tasks", pk=ot.id)
        messages.error(request, "Corrige los errores en el formulario.")
    else:
        formset = TaskFormSet(instance=ot, prefix="tasks")
        evidset = EvidenceURLFormSet(instance=ot, prefix="evid")

    return render(request, "workorders/task_formset.html", {
        "ot": ot, "formset": formset, "evidset": evidset
    })


# =======================
# HTML: Hook para el Admin (Evidencia URL)
# =======================
@require_http_methods(["POST"])
def add_evidence_url_from_admin(request, pk: int):
    """
    Endpoint que recibe POST desde el template de admin de la OT
    para agregar una evidencia por URL sin pelearse con el POST del admin.
    """
    ot = get_object_or_404(WorkOrder, pk=pk)
    formset = EvidenceURLFormSet(request.POST, instance=ot, prefix="evid_admin")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Evidencia registrada.")
    else:
        messages.error(request, "URL inválida o faltan datos.")
    # Regresa al admin de la OT
    return redirect(reverse("admin:workorders_workorder_change", args=[pk]))
