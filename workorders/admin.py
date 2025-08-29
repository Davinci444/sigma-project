"""Admin de Órdenes de Trabajo: UX diferenciada por tipo, inlines y lista robusta."""

from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from datetime import datetime

from .models import (
    WorkOrder,
    WorkOrderTask,
    WorkOrderPart,
    WorkOrderNote,
    WorkOrderAttachment,
    WorkOrderDriver,
    MaintenanceCategory,
    MaintenanceSubcategory,
    MaintenanceManual,
    ManualTask,
    MaintenancePlan,
    ProbableCause,
)

# -----------------------------
# FORM de validación ligera
# -----------------------------
class WorkOrderAdminForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        ot = cleaned.get("order_type")
        pre_diag = cleaned.get("pre_diagnosis")
        probable_causes = cleaned.get("probable_causes")

        if ot == WorkOrder.OrderType.CORRECTIVE:
            if not (pre_diag or (probable_causes and probable_causes.exists())):
                raise forms.ValidationError(
                    "Para OT Correctiva debes diligenciar el Pre-diagnóstico o al menos una Causa Probable."
                )
        else:
            # Limpiar campos correctivos si por error vinieron en el POST
            cleaned["pre_diagnosis"] = ""
            cleaned["failure_origin"] = None
            cleaned["severity"] = None
            cleaned["requires_approval"] = False
            cleaned["out_of_service"] = False
            cleaned["warranty_covered"] = False
            cleaned["probable_causes"] = []

        return cleaned


# -----------------------------
# INLINES
# -----------------------------
class WorkOrderDriverInline(admin.TabularInline):
    model = WorkOrderDriver
    extra = 0
    autocomplete_fields = ("driver",)
    fields = ("driver", "responsibility_percent")
    verbose_name = "Conductor responsable"
    verbose_name_plural = "Conductores responsables"


class WorkOrderAttachmentInline(admin.TabularInline):
    model = WorkOrderAttachment
    extra = 0
    fields = ("url", "description", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Adjunto"
    verbose_name_plural = "Adjuntos"


class WorkOrderNoteInline(admin.TabularInline):
    model = WorkOrderNote
    extra = 0
    fields = ("visibility", "text", "author", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    verbose_name = "Novedad / Comentario"
    verbose_name_plural = "Novedades / Comentarios"


class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 0
    autocomplete_fields = ("category", "subcategory")
    fields = ("category", "subcategory", "description", "hours_spent", "is_external", "labor_rate")
    verbose_name = "Trabajo"
    verbose_name_plural = "Trabajos"


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 0
    autocomplete_fields = ("part",)
    fields = ("part", "quantity", "cost_at_moment")
    verbose_name = "Repuesto usado"
    verbose_name_plural = "Repuestos usados"


# -----------------------------
# Filtro “¿En taller?”
# -----------------------------
class InWorkshopFilter(admin.SimpleListFilter):
    title = "¿En taller?"
    parameter_name = "in_workshop"

    def lookups(self, request, model_admin):
        return (("yes", "Sí"), ("no", "No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                check_in_at__isnull=False
            ).exclude(
                status__in=[
                    WorkOrder.OrderStatus.VERIFIED,
                    WorkOrder.OrderStatus.CANCELLED,
                    WorkOrder.OrderStatus.COMPLETED,
                ]
            )
        if self.value() == "no":
            return queryset.filter(
                check_in_at__isnull=True
            ) | queryset.filter(
                status__in=[
                    WorkOrder.OrderStatus.VERIFIED,
                    WorkOrder.OrderStatus.CANCELLED,
                    WorkOrder.OrderStatus.COMPLETED,
                ]
            )
        return queryset


# -----------------------------
# Acción exportar CSV
# -----------------------------
def exportar_ot_csv(modeladmin, request, queryset):
    filename = f"ordenes_trabajo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    w = csv.writer(resp)
    w.writerow([
        "ID", "Placa", "Tipo", "Estado", "Prioridad", "Severidad",
        "Gestor", "Programado_Inicio", "Programado_Fin",
        "Ingreso", "Salida", "KM_Atencion",
        "Costo_MO_Int", "Costo_MO_Ext", "Costo_Repuestos", "Fecha_Creacion"
    ])
    for obj in queryset.select_related("vehicle", "assigned_technician"):
        gestor = ""
        if obj.assigned_technician:
            full = getattr(obj.assigned_technician, "get_full_name", lambda: "")() or ""
            gestor = full or getattr(obj.assigned_technician, "username", "") or str(obj.assigned_technician)
        w.writerow([
            obj.pk,
            getattr(obj.vehicle, "plate", ""),
            obj.get_order_type_display(),
            obj.get_status_display(),
            obj.get_priority_display(),
            obj.get_severity_display() if obj.severity else "",
            gestor,
            obj.scheduled_start or "",
            obj.scheduled_end or "",
            obj.check_in_at or "",
            obj.check_out_at or "",
            obj.odometer_at_service or "",
            obj.labor_cost_internal,
            obj.labor_cost_external,
            obj.parts_cost,
            obj.created_at,
        ])
    return resp
exportar_ot_csv.short_description = "Exportar selección a CSV"


# -----------------------------
# ADMIN principal
# -----------------------------
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    form = WorkOrderAdminForm
    actions = [exportar_ot_csv]

    # Lista
    list_display = (
        "id", "vehicle_plate", "order_type", "status_badge",
        "priority", "severity", "assigned_technician_name", "created_at",
    )
    list_select_related = ("vehicle", "assigned_technician")
    list_filter = (
        "order_type", "status", "priority", "severity",
        "failure_origin", "out_of_service", "warranty_covered",
        InWorkshopFilter,
        ("vehicle", admin.RelatedOnlyFieldListFilter),
        ("assigned_technician", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("vehicle__plate", "description", "id")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    readonly_fields = ("created_at",)
    autocomplete_fields = ("vehicle", "assigned_technician")
    save_on_top = True

    inlines = [
        WorkOrderDriverInline,
        WorkOrderAttachmentInline,
        WorkOrderNoteInline,
        WorkOrderTaskInline,
        WorkOrderPartInline,
    ]

    # Helpers de columnas
    def vehicle_plate(self, obj):
        return getattr(obj.vehicle, "plate", "—")
    vehicle_plate.short_description = "Placa"

    def assigned_technician_name(self, obj):
        u = obj.assigned_technician
        if not u:
            return "—"
        full = getattr(u, "get_full_name", lambda: "")() or ""
        return full or getattr(u, "username", None) or str(u)
    assigned_technician_name.short_description = "Técnico / Gestor"

    def status_badge(self, obj):
        color = {
            WorkOrder.OrderStatus.SCHEDULED: "#1f7aec",
            WorkOrder.OrderStatus.IN_RECEPTION: "#8f6bf1",
            WorkOrder.OrderStatus.IN_SERVICE: "#f0ad4e",
            WorkOrder.OrderStatus.WAITING_PART: "#e67e22",
            WorkOrder.OrderStatus.PENDING_APPROVAL: "#c0392b",
            WorkOrder.OrderStatus.STOPPED_BY_CLIENT: "#7f8c8d",
            WorkOrder.OrderStatus.IN_ROAD_TEST: "#16a085",
            WorkOrder.OrderStatus.COMPLETED: "#2ecc71",
            WorkOrder.OrderStatus.VERIFIED: "#27ae60",
            WorkOrder.OrderStatus.CANCELLED: "#95a5a6",
        }.get(obj.status, "#999")
        return format_html(
            '<span style="padding:2px 8px;border-radius:10px;background:{};color:#fff;font-size:12px;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "Estado"

    # Fieldsets dinámicos
    BASE_FIELDS = (
        ("Información básica", {
            "classes": ("sigma-base",),
            "fields": (
                "order_type", "vehicle", "description",
                ("priority", "status"),
                ("assigned_technician", "created_at"),
                ("scheduled_start", "scheduled_end"),
                ("check_in_at", "check_out_at"),
                "odometer_at_service",
            )
        }),
    )
    PREVENTIVE_EXTRA = (
        ("Plan preventivo (referencia)", {
            "classes": ("collapse", "sigma-preventive-only"),
            "description": "Se activa y actualiza automáticamente al cerrar la primera OT preventiva.",
            "fields": ()
        }),
    )
    CORRECTIVE_EXTRA = (
        ("Diagnóstico", {
            "classes": ("sigma-corrective-only",),
            "fields": (
                "pre_diagnosis",
                ("failure_origin", "severity"),
                ("out_of_service", "requires_approval", "warranty_covered"),
                "probable_causes",
            )
        }),
    )

    def _order_type_from_request(self, request, obj):
        if obj:
            return obj.order_type
        ot = request.POST.get("order_type") or request.GET.get("order_type")
        if ot in dict(WorkOrder.OrderType.choices):
            return ot
        return WorkOrder.OrderType.CORRECTIVE

    def get_fieldsets(self, request, obj=None):
        ot = self._order_type_from_request(request, obj)
        if ot == WorkOrder.OrderType.PREVENTIVE:
            return self.BASE_FIELDS + self.PREVENTIVE_EXTRA
        return self.BASE_FIELDS + self.CORRECTIVE_EXTRA

    def get_exclude(self, request, obj=None):
        ot = self._order_type_from_request(request, obj)
        if ot == WorkOrder.OrderType.PREVENTIVE:
            return ("pre_diagnosis", "failure_origin", "severity",
                    "out_of_service", "requires_approval", "warranty_covered",
                    "probable_causes")
        return ()

    class Media:
        # Este JS solo oculta/mostrar secciones; si no existe, la página carga igual.
        js = ("workorders/admin_workorder.js",)


# -----------------------------
# Resto de modelos
# -----------------------------
@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(MaintenanceSubcategory)
class MaintenanceSubcategoryAdmin(admin.ModelAdmin):
    autocomplete_fields = ("category",)
    search_fields = ("name", "category__name")
    list_display = ("name", "category")


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("name", "fuel_type")
    list_filter = ("fuel_type",)
    search_fields = ("name",)


@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    autocomplete_fields = ("manual",)
    list_display = ("manual", "km_interval", "description")
    list_filter = ("manual",)
    search_fields = ("description",)


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    autocomplete_fields = ("vehicle", "manual")
    list_display = ("vehicle", "manual", "is_active", "last_service_km", "last_service_date")
    list_filter = ("is_active", "manual__fuel_type")
    search_fields = ("vehicle__plate",)


@admin.register(ProbableCause)
class ProbableCauseAdmin(admin.ModelAdmin):
    search_fields = ("name", "description")
    list_display = ("name",)
