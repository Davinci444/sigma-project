# workorders/views.py
"""Vistas API y HTML (unificadas) para órdenes de trabajo."""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from rest_framework import viewsets

from .models import WorkOrder, MaintenancePlan, WorkOrderTask, WorkOrderPart
from .serializers import (
    WorkOrderSerializer,
    MaintenancePlanSerializer,
    WorkOrderTaskSerializer,
    WorkOrderPartSerializer,
)
from .forms import (
    WorkOrderUnifiedForm, TaskFormSet,
    QuickCreateVehicleForm, QuickCreateDriverForm,
    QuickCreateCategoryForm, QuickCreateSubcategoryForm
)

logger = logging.getLogger(__name__)

# ========= API (intacto) =========
class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all().prefetch_related("tasks", "parts_used", "notes")
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
    """Una sola pantalla: datos base, conductor, (correctivo) prediagnóstico/origen/severidad,
    tareas (categoría/subcategoría) y novedades. SIN evidencias."""
    ot = get_object_or_404(WorkOrder, pk=pk) if pk else None

    # ---- Quick-Create (crear sin salir) ----
    if request.method == "POST" and request.POST.get("qc_target"):
        target = request.POST.get("qc_target")
        try:
            if target == "vehicle":
                form = QuickCreateVehicleForm(request.POST)
                if form.is_valid():
                    obj = form.save()
                    messages.success(request, f"Vehículo {obj} creado.")
                else:
                    messages.error(request, "No se pudo crear el vehículo. Revisa los campos.")
            elif target == "driver":
                form = QuickCreateDriverForm(request.POST)
                if form.is_valid():
                    obj = form.save()
                    messages.success(request, "Conductor creado.")
                else:
                    messages.error(request, "No se pudo crear el conductor. Revisa los campos.")
            elif target == "category":
                form = QuickCreateCategoryForm(request.POST)
                if form.is_valid():
                    obj = form.save()
                    messages.success(request, "Categoría creada.")
                else:
                    messages.error(request, "No se pudo crear la categoría. Revisa los campos.")
            elif target == "subcategory":
                form = QuickCreateSubcategoryForm(request.POST)
                if form.is_valid():
                    obj = form.save()
                    messages.success(request, "Subcategoría creada.")
                else:
                    messages.error(request, "No se pudo crear la subcategoría. Revisa los campos.")
            else:
                messages.error(request, "Acción no reconocida.")
        except Exception as e:
            logger.exception("Quick-Create falló: %s", e)
            messages.error(request, "Error al crear. Verifica los campos mínimos requeridos del modelo.")
        return redirect(request.path if not pk else f"/api/workorders/workorders/{pk}/edit/")

    # ---- Flujo normal crear/editar OT ----
    if request.method == "POST":
        try:
            form = WorkOrderUnifiedForm(request.POST, instance=ot)
            if ot:
                task_fs = TaskFormSet(request.POST, instance=ot, prefix="tasks")
            else:
                task_fs = None

            if form.is_valid():
                ot_saved = form.save(user=request.user)
                if task_fs is None:
                    task_fs = TaskFormSet(request.POST, instance=ot_saved, prefix="tasks")

                if task_fs.is_valid():
                    task_fs.save()

                    if hasattr(ot_saved, "recalculate_costs"):
                        try:
                            ot_saved.recalculate_costs()
                        except Exception as e:
                            logger.warning("recalculate_costs falló: %s", e)

                    from django.contrib import messages
                    messages.success(request, f"OT #{ot_saved.id} guardada correctamente.")
                    return redirect("workorders_unified_edit", pk=ot_saved.id)
                else:
                    messages.error(request, "Corrige los errores en Tareas.")
                    ot = ot_saved  # re-render
            else:
                messages.error(request, "Revisa los datos de la Orden de Trabajo.")
        except Exception as e:
            logger.exception("Error al procesar OT unificada: %s", e)
            messages.error(request, "Se produjo un error al guardar la OT. Revisa los datos y vuelve a intentar.")
            form = WorkOrderUnifiedForm(request.POST, instance=ot)
            task_fs = TaskFormSet(request.POST, instance=ot or None, prefix="tasks")
    else:
        form = WorkOrderUnifiedForm(instance=ot)
        task_fs = TaskFormSet(instance=ot, prefix="tasks") if ot else TaskFormSet(prefix="tasks")

    notes = ot.notes.order_by("-created_at") if ot and hasattr(ot, "notes") else []

    # Campos datetime “reales” presentes
    datetime_real_fields = [f for f in WorkOrderUnifiedForm.dynamic_datetime_fields if f in form.fields]

    # Quick-create forms vacíos (solo si sus modelos existen)
    qc_vehicle = QuickCreateVehicleForm() if QuickCreateVehicleForm._meta.fields else None
    qc_driver = QuickCreateDriverForm() if QuickCreateDriverForm._meta.fields else None
    qc_category = QuickCreateCategoryForm() if QuickCreateCategoryForm._meta.fields else None
    qc_subcategory = QuickCreateSubcategoryForm() if QuickCreateSubcategoryForm._meta.fields else None

    return render(request, "workorders/order_full_form.html", {
        "form": form,
        "task_fs": task_fs,
        "notes": notes,
        "ot": ot,
        "datetime_real_fields": datetime_real_fields,
        "qc_vehicle": qc_vehicle,
        "qc_driver": qc_driver,
        "qc_category": qc_category,
        "qc_subcategory": qc_subcategory,
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


# ========= Programación (se conserva) =========
from django.utils import timezone
from collections import defaultdict

@staff_member_required
def schedule_view(request):
    qs = (WorkOrder.objects
          .select_related("vehicle")
          .order_by("scheduled_start", "priority", "id"))
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
