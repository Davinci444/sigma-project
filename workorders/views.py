# workorders/views.py
"""Vistas API y HTML (unificadas) para órdenes de trabajo."""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from rest_framework import viewsets, filters

from .models import (
    WorkOrder,
    MaintenancePlan,
    WorkOrderTask,
    WorkOrderPart,
    MaintenanceCategory,
    MaintenanceSubcategory,
)
from .serializers import (
    WorkOrderSerializer,
    MaintenancePlanSerializer,
    WorkOrderTaskSerializer,
    WorkOrderPartSerializer,
    MaintenanceCategorySerializer,
    MaintenanceSubcategorySerializer,
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


class MaintenanceCategoryViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceCategory.objects.all()
    serializer_class = MaintenanceCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class MaintenanceSubcategoryViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceSubcategory.objects.select_related("category")
    serializer_class = MaintenanceSubcategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "category__name"]


# ========= VISTA UNIFICADA =========
@staff_member_required
def workorder_unified(request, pk=None):
    """Una sola pantalla: datos base, conductor, (correctivo) prediagnóstico/origen/severidad,
    tareas (categoría/subcategoría) y novedades. SIN evidencias."""
    ot = get_object_or_404(WorkOrder, pk=pk) if pk else None

    # Tipo inicial según OT existente o querystring
    initial = {}
    if not ot:
        t = request.GET.get("type", "")
        if t.lower().startswith("corr"):
            initial["order_type"] = WorkOrder.OrderType.CORRECTIVE
        elif t.lower().startswith("prev"):
            initial["order_type"] = WorkOrder.OrderType.PREVENTIVE

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
        return redirect(request.path if not pk else request.path)

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

                    # Redirección por nombre según el prefijo de la ruta
                    dest = "workorders_admin_edit" if request.path.startswith("/admin/") else "workorders_unified_edit"
                    messages.success(request, f"OT #{ot_saved.id} guardada correctamente.")
                    return redirect(dest, pk=ot_saved.id)
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
        form = WorkOrderUnifiedForm(instance=ot, initial=initial)
        task_fs = TaskFormSet(instance=ot, prefix="tasks") if ot else TaskFormSet(prefix="tasks")

    notes = ot.notes.order_by("-created_at") if ot and hasattr(ot, "notes") else []

    # BoundFields de los datetime “reales” (para no usar form[fname] en plantilla)
    datetime_real_names = [f for f in form.dynamic_datetime_fields if f in form.fields]
    dynamic_dt_bfs = [form[name] for name in datetime_real_names]

    ot_value = form.data.get("order_type") if form.is_bound else (
        form.initial.get("order_type") or getattr(ot, "order_type", "")
    )
    show_corrective = str(ot_value).upper().startswith("CORRECT")

    # Manual de mantenimiento del vehículo seleccionado
    vehicle_id = (
        request.POST.get("vehicle")
        or request.GET.get("vehicle")
        or (ot.vehicle_id if ot else None)
    )
    manual = None
    if vehicle_id:
        plan = (
            MaintenancePlan.objects
            .filter(vehicle_id=vehicle_id)
            .select_related("manual")
            .first()
        )
        if plan:
            manual = plan.manual

    return render(request, "workorders/order_full_form.html", {
        "form": form,
        "task_fs": task_fs,
        "notes": notes,
        "ot": ot,
        "dynamic_dt_bfs": dynamic_dt_bfs,  # ← usar esto en la plantilla
        "title": ("Editar OT" if ot else "Nueva OT"),
        "manual": manual,
        "show_corrective": show_corrective,
        # Quick-create forms (si existen)
        "qc_vehicle": QuickCreateVehicleForm() if QuickCreateVehicleForm._meta.fields else None,
        "qc_driver": QuickCreateDriverForm() if QuickCreateDriverForm._meta.fields else None,
        "qc_category": QuickCreateCategoryForm() if QuickCreateCategoryForm._meta.fields else None,
        "qc_subcategory": QuickCreateSubcategoryForm() if QuickCreateSubcategoryForm._meta.fields else None,
        "is_admin": request.path.startswith("/admin/"),
    })


# ========= Compatibilidad/rutas viejas: redirigen aquí =========
@require_http_methods(["GET", "POST"])
def new_preventive(request):
    return redirect(f"{reverse('workorders_unified_new')}?type=preventive")

@require_http_methods(["GET", "POST"])
def new_corrective(request):
    return redirect(f"{reverse('workorders_unified_new')}?type=corrective")

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
