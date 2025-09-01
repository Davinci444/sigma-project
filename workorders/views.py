# workorders/views.py
"""Vistas API y HTML para órdenes de trabajo."""

from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from rest_framework import viewsets

from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
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
@staff_member_required
def schedule_view(request):
    """
    Muestra OTs agrupadas por estado lógico:
    - Programadas (SCHEDULED)
    - En taller (IN_RECEPTION / IN_SERVICE / WAITING_PART / PENDING_APPROVAL / STOPPED_BY_CLIENT / IN_ROAD_TEST / DIAGNOSIS)
    """
    in_shop_status = [
        WorkOrder.OrderStatus.IN_RECEPTION,
        WorkOrder.OrderStatus.IN_SERVICE,
        WorkOrder.OrderStatus.WAITING_PART,
        WorkOrder.OrderStatus.PENDING_APPROVAL,
        WorkOrder.OrderStatus.STOPPED_BY_CLIENT,
        WorkOrder.OrderStatus.IN_ROAD_TEST,
        getattr(WorkOrder.OrderStatus, "DIAGNOSIS", WorkOrder.OrderStatus.IN_SERVICE),
    ]

    scheduled = (WorkOrder.objects
                 .filter(status=WorkOrder.OrderStatus.SCHEDULED)
                 .select_related("vehicle")
                 .order_by("scheduled_start", "priority", "id"))

    in_shop = (WorkOrder.objects
               .filter(status__in=in_shop_status)
               .select_related("vehicle")
               .order_by("scheduled_start", "priority", "id"))

    return render(request, "workorders/schedule.html", {
        "scheduled": scheduled,
        "in_shop": in_shop,
        "title": "Programación por Estado",
    })


# =======================
# HTML: Crear OT (Preventiva / Correctiva)
# =======================
@staff_member_required
def new_preventive(request):
    if request.method == "POST":
        form = WorkOrderPreventiveForm(request.POST)
        if form.is_valid():
            ot = form.save(user=request.user)
            messages.success(request, f"OT Preventiva #{ot.id} creada.")
            return redirect("workorders_edit_tasks", pk=ot.id)
        messages.error(request, "Revisa el formulario.")
    else:
        form = WorkOrderPreventiveForm()
    return render(request, "workorders/order_form.html", {"form": form, "title": "Nueva OT Preventiva"})

@staff_member_required
def new_corrective(request):
    if request.method == "POST":
        form = WorkOrderCorrectiveForm(request.POST)
        if form.is_valid():
            ot = form.save(user=request.user)
            messages.success(request, f"OT Correctiva #{ot.id} creada.")
            return redirect("workorders_edit_tasks", pk=ot.id)
        messages.error(request, "Revisa el formulario.")
    else:
        form = WorkOrderCorrectiveForm()
    return render(request, "workorders/order_form.html", {"form": form, "title": "Nueva OT Correctiva"})


# =======================
# HTML: Agregar/Editar Tareas + Evidencias URL
# =======================
@staff_member_required
def edit_tasks(request, pk: int):
    ot = get_object_or_404(WorkOrder, pk=pk)
    if request.method == "POST":
        formset = TaskFormSet(request.POST, instance=ot, prefix="tasks")
        evidset = EvidenceURLFormSet(request.POST, instance=ot, prefix="evid")
        if formset.is_valid() and evidset.is_valid():
            formset.save()
            evidset.save()
            ot.recalculate_costs()
            messages.success(request, "Tareas y evidencias actualizadas.")
            return redirect("workorders_edit_tasks", pk=ot.id)
        messages.error(request, "Corrige los errores resaltados.")
    else:
        formset = TaskFormSet(instance=ot, prefix="tasks")
        evidset = EvidenceURLFormSet(instance=ot, prefix="evid")
    return render(request, "workorders/task_formset.html", {"ot": ot, "formset": formset, "evidset": evidset})


# =======================
# HTML: Hook simple desde admin (opcional)
# =======================
@require_http_methods(["POST"])
@staff_member_required
def add_evidence_url_from_admin(request, pk: int):
    ot = get_object_or_404(WorkOrder, pk=pk)
    formset = EvidenceURLFormSet(request.POST, instance=ot, prefix="evid_admin")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Evidencia registrada.")
    else:
        messages.error(request, "URL inválida o faltan datos.")
    return redirect(reverse("admin:workorders_workorder_change", args=[pk]))
