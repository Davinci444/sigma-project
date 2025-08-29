"""Admin robusto y estable:
   - Catálogos visibles.
   - WorkOrder base mínimo.
   - Proxies Preventiva/Correctiva.
   - Inlines (Notas, Adjuntos, Responsables) SOLO en edición para evitar 500 en /add/.
   - IMPORTANTE: Como WorkOrder.drivers usa through=WorkOrderDriver, NO se incluye en fieldsets ni filter_horizontal.
"""

from django.contrib import admin
from .models import (
    MaintenanceCategory,
    MaintenanceSubcategory,
    MaintenanceManual,
    ManualTask,
    MaintenancePlan,
    WorkOrder,
    WorkOrderTask,
    WorkOrderPart,
    ProbableCause,
    WorkOrderNote,
    WorkOrderAttachment,
    WorkOrderDriver,
)
from .proxies import PreventiveOrder, CorrectiveOrder


# -------------------------
# Catálogos
# -------------------------

@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(MaintenanceSubcategory)
class MaintenanceSubcategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    list_filter = ("category",)
    search_fields = ("name", "category__name")
    autocomplete_fields = ("category",)


@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "fuel_type")
    list_filter = ("fuel_type",)
    search_fields = ("name",)


@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "manual", "description", "km_interval")
    list_filter = ("manual",)
    search_fields = ("description", "manual__name")
    autocomplete_fields = ("manual",)


@admin.register(ProbableCause)
class ProbableCauseAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# -------------------------
# Planes
# -------------------------

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle", "manual", "is_active", "last_service_km", "last_service_date")
    list_filter = ("is_active", "manual")
    search_fields = ("vehicle__plate", "manual__name")
    raw_id_fields = ("vehicle", "manual")
    list_select_related = ("vehicle", "manual")
    date_hierarchy = "last_service_date"


# -------------------------
# Inlines (solo en edición)
# -------------------------

class WorkOrderNoteInline(admin.TabularInline):
    model = WorkOrderNote
    extra = 0
    fields = ("created_at", "author", "visibility", "text")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


class WorkOrderAttachmentInline(admin.TabularInline):
    model = WorkOrderAttachment
    extra = 0
    fields = ("created_at", "url", "description")
    readonly_fields = ("created_at",)


class WorkOrderDriverInline(admin.TabularInline):
    """M2M through para Conductores (permite % de responsabilidad)."""
    model = WorkOrderDriver
    extra = 0
    autocomplete_fields = ("driver",)
    fields = ("driver", "responsibility_percent")


# -------------------------
# WorkOrder base (mínimo)
# -------------------------

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "order_type", "status", "vehicle", "scheduled_start")
    list_filter = (
        "order_type",
        "status",
        "severity",
        "failure_origin",
        "warranty_covered",
        "requires_approval",
        "out_of_service",
    )
    search_fields = ("id", "vehicle__plate", "description", "pre_diagnosis")
    raw_id_fields = ("vehicle", "assigned_technician")
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    fieldsets = (
        ("General", {
            "fields": (
                "order_type", "status", "vehicle", "priority", "assigned_technician",
                "description",
            )
        }),
        ("Programación y Tiempos", {
            "fields": ("scheduled_start", "scheduled_end", "check_in_at", "check_out_at", "odometer_at_service")
        }),
        ("Correctivas (opcional)", {
            "fields": ("pre_diagnosis", "severity", "failure_origin", "probable_causes",
                       "warranty_covered", "requires_approval", "out_of_service"),
            "classes": ("collapse",),
        }),
        ("Costos", {
            "fields": ("labor_cost_internal", "labor_cost_external", "parts_cost"),
            "classes": ("collapse",),
        }),
    )
    filter_horizontal = ("probable_causes",)  # OJO: drivers NO va aquí (usa through)

    def get_inline_instances(self, request, obj=None):
        # Para que la página /add/ NO cargue inlines (evita 500).
        if obj is None:
            return []
        # En base, por defecto no agregamos inlines para mantenerlo mínimo.
        return super().get_inline_instances(request, obj)


# -------------------------
# Proxies
# -------------------------

@admin.register(PreventiveOrder)
class PreventiveOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "vehicle", "scheduled_start")
    list_filter = ("status",)
    search_fields = ("id", "vehicle__plate")
    raw_id_fields = ("vehicle", "assigned_technician")
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    fieldsets = (
        ("Preventiva", {
            "fields": ("status", "vehicle", "priority", "assigned_technician", "description")
        }),
        ("Programación y Tiempos", {
            "fields": ("scheduled_start", "scheduled_end", "check_in_at", "check_out_at", "odometer_at_service")
        }),
        ("Costos", {
            "fields": ("labor_cost_internal", "labor_cost_external", "parts_cost"),
            "classes": ("collapse",),
        }),
    )
    # Nada de filter_horizontal para drivers (usa through)
    inlines = [WorkOrderDriverInline]  # Solo en edición (se filtra abajo)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(order_type=WorkOrder.OrderType.PREVENTIVE)

    def save_model(self, request, obj, form, change):
        obj.order_type = WorkOrder.OrderType.PREVENTIVE
        super().save_model(request, obj, form, change)

    def get_inline_instances(self, request, obj=None):
        # Evita inlines en /add/ para no romper.
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(CorrectiveOrder)
class CorrectiveOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "vehicle", "severity", "failure_origin", "scheduled_start")
    list_filter = ("status", "severity", "failure_origin", "warranty_covered", "requires_approval", "out_of_service")
    search_fields = ("id", "vehicle__plate", "description", "pre_diagnosis")
    raw_id_fields = ("vehicle", "assigned_technician")
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    fieldsets = (
        ("Correctiva", {
            "fields": ("status", "vehicle", "priority", "assigned_technician", "description")
        }),
        ("Diagnóstico Inicial", {
            "fields": ("pre_diagnosis", "severity", "failure_origin", "probable_causes")
        }),
        ("Estado / Flags", {
            "fields": ("warranty_covered", "requires_approval", "out_of_service")
        }),
        ("Programación y Tiempos", {
            "fields": ("scheduled_start", "scheduled_end", "check_in_at", "check_out_at", "odometer_at_service")
        }),
        ("Costos", {
            "fields": ("labor_cost_internal", "labor_cost_external", "parts_cost"),
            "classes": ("collapse",),
        }),
    )
    filter_horizontal = ("probable_causes",)  # drivers NO va aquí (usa through)
    inlines = [WorkOrderDriverInline, WorkOrderNoteInline, WorkOrderAttachmentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(order_type=WorkOrder.OrderType.CORRECTIVE)

    def save_model(self, request, obj, form, change):
        obj.order_type = WorkOrder.OrderType.CORRECTIVE
        super().save_model(request, obj, form, change)

    def get_inline_instances(self, request, obj=None):
        # Solo mostrar inlines cuando ya existe la OT (modo edición)
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)
