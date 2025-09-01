# workorders/admin.py
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse, HttpRequest
from django.db.models import Q
from typing import List

from .models import (
    WorkOrder,
    WorkOrderNote,
    MaintenanceManual,
    ManualTask,
    WorkOrderTask,
)

# Optional imports guarded later
try:
    from .models import MaintenanceCategory, MaintenanceSubcategory
except Exception:  # pragma: no cover - if models are partially defined
    MaintenanceCategory = None
    MaintenanceSubcategory = None


def _existing_fk_fields(model, candidates: List[str]) -> List[str]:
    out = []
    for name in candidates:
        try:
            model._meta.get_field(name)
            out.append(name)
        except Exception:
            continue
    return out


class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter subcategories by category within inline rows (best effort)
        if MaintenanceSubcategory and db_field.name in ("subcategory", "sub_category", "subcategoria"):
            qs = MaintenanceSubcategory.objects.all()
            # Try to read raw category value from the posted formset row (category field id ends with -category)
            cat_id = None
            for key, val in request.POST.items():
                if key.endswith("-category") and val:
                    cat_id = val
                    break
                if key.endswith("-categoria") and val:
                    cat_id = val
                    break
            if cat_id:
                try:
                    qs = qs.filter(Q(category_id=cat_id) | Q(categoria_id=cat_id))
                except Exception:
                    qs = qs.filter(category_id=cat_id)
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    # Use a unified change form template for BOTH add & change so it "looks the same"
    change_form_template = "admin/workorders/workorder/change_form.html"
    add_form_template = "admin/workorders/workorder/change_form.html"

    list_display = ("id", "vehicle", "order_type", "status", "priority", "scheduled_start", "scheduled_end")
    list_select_related = ("vehicle",)
    ordering = ("-id",)
    search_fields = ("id", "vehicle__plate", "vehicle__vin")
    list_filter = ("order_type", "status", "priority")
    inlines = [WorkOrderTaskInline]

    # Show the magnifying glass on heavy relations (safe/dynamic)
    raw_id_fields = tuple(_existing_fk_fields(WorkOrder, ["vehicle", "assigned_to", "external_vendor", "driver"]))

    fieldsets = (
        ("Datos base", {
            "fields": tuple(
                f for f in [
                    "order_type", "vehicle", "description",
                ] if f in [fld.name for fld in WorkOrder._meta.get_fields()]
            )
        }),
        ("Fechas y odómetro", {
            "fields": tuple(
                f for f in [
                    "scheduled_start", "scheduled_end", "actual_start", "actual_end", "odometer_at_service",
                ] if f in [fld.name for fld in WorkOrder._meta.get_fields()]
            )
        }),
        ("Clasificación", {
            "fields": tuple(
                f for f in [
                    "category", "subcategory", "priority", "status",
                ] if f in [fld.name for fld in WorkOrder._meta.get_fields()]
            )
        }),
        ("Costos (si aplica)", {
            "fields": tuple(
                f for f in [
                    "is_external", "external_vendor", "external_cost", "labor_cost", "parts_cost", "total_cost",
                ] if f in [fld.name for fld in WorkOrder._meta.get_fields()]
            )
        }),
        ("Asignación (si aplica)", {
            "fields": tuple(
                f for f in [
                    "assigned_to", "driver", "driver_responsibility",
                ] if f in [fld.name for fld in WorkOrder._meta.get_fields()]
            )
        }),
    )

    class Media:
        js = (
            "workorders/js/select2.min.js",   # si ya está en tu static, lo aprovechamos
            "workorders/admin_workorder.js",
        )
        css = {"all": ("workorders/css/select2.min.css", )}

    def get_urls(self):
        urls = super().get_urls()
        custom = []
        # JSON endpoint for dependent subcategories
        if MaintenanceSubcategory:
            custom.append(
                path("subcategories/", self.admin_site.admin_view(self.subcategories_view), name="workorder_subcategories")
            )
        return custom + urls

    def subcategories_view(self, request: HttpRequest):
        if not MaintenanceSubcategory:
            return JsonResponse([], safe=False)
        cat_id = request.GET.get("category")
        qs = MaintenanceSubcategory.objects.all()
        if cat_id:
            try:
                qs = qs.filter(Q(category_id=cat_id) | Q(categoria_id=cat_id))
            except Exception:
                qs = qs.filter(category_id=cat_id)
        qs = qs.order_by("name" if hasattr(MaintenanceSubcategory, "name") else "id")
        data = [{"id": obj.pk, "text": getattr(obj, "name", str(obj))} for obj in qs[:500]]
        return JsonResponse(data, safe=False)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Server-side initial filter for subcategory based on selected category (if present in POST/GET)
        if MaintenanceSubcategory and db_field.name in ("subcategory", "sub_category", "subcategoria"):
            cat = request.POST.get("category") or request.GET.get("category")
            if cat:
                qs = MaintenanceSubcategory.objects.all()
                try:
                    qs = qs.filter(Q(category_id=cat) | Q(categoria_id=cat))
                except Exception:
                    qs = qs.filter(category_id=cat)
                kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "work_order", "author", "created_at")
    search_fields = ("work_order__id", "text")
    list_select_related = ("work_order", "author")

    def get_list_display(self, request):
        # in case 'author' field doesn't exist in model in some deployments
        fields = ["id", "work_order", "created_at"]
        try:
            WorkOrderNote._meta.get_field("author")
            fields.insert(2, "author")
        except Exception:
            pass
        return tuple(fields)


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "manual", "category", "subcategory", "km_interval", "months_interval")
    list_filter = ("manual",)
    search_fields = ("category__name", "subcategory__name")
