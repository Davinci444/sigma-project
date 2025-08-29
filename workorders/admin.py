"""Admin de Órdenes de Trabajo y Taxonomía (estable y sin sorpresas)."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django import forms

from .models import (
    MaintenanceManual,
    ManualTask,
    MaintenanceCategory,
    MaintenanceSubcategory,
    MaintenancePlan,
    WorkOrder,
    WorkOrderTask,
    WorkOrderPart,
    ProbableCause,
    WorkOrderDriver,
    WorkOrderNote,
    WorkOrderAttachment,
)


# ---------------------------
# Taxonomía / Manuales
# ---------------------------

@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("name", "fuel_type")
    search_fields = ("name",)
    list_filter = ("fuel_type",)


@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    list_display = ("manual", "km_interval", "description")
    list_filter = ("manual",)
    search_fields = ("description",)


@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(MaintenanceSubcategory)
class MaintenanceSubcategoryAdmin(admin.ModelAdmin):
    list_display = ("category", "name", "description")
    list_filter = ("category",)
    search_fields = ("name", "category__name")


@admin.register(ProbableCause)
class ProbableCauseAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "manual", "is_active", "last_service_km", "last_service_date")
    list_filter = ("is_active", "manual__fuel_type")
    search_fields = ("vehicle__plate", "manual__name")


# ---------------------------
# Inlines para OT
# ---------------------------

class WorkOrderDriverInline(admin.TabularInline):
    """
    Inline para asignar Conductores responsables a la OT.
    Usa el modelo intermedio (through) WorkOrderDriver.
    """
    model = WorkOrderDriver
    extra = 1
    autocomplete_fields = ["driver"]
    fields = ("driver", "responsibility_percent")
    verbose_name = "Conductor responsable"
    verbose_name_plural = "Conductores responsables"


class WorkOrderNoteInline(admin.TabularInline):
    """
    Inline de Novedades/Notas de la OT.
    El autor se completa al guardar (si ya tienes esa lógica en admin or save_model,
    puedes dejar editable; si no, lo dejamos visible y editable).
    """
    model = WorkOrderNote
    extra = 0
    fields = ("visibility", "text", "author", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    verbose_name = "Novedad / Comentario"
    verbose_name_plural = "Novedades / Comentarios"


class WorkOrderAttachmentInline(admin.TabularInline):
    model = WorkOrderAttachment
    extra = 0
    fields = ("url", "description", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Adjunto"
    verbose_name_plural = "Adjuntos"


# Estos modelos siguen existiendo pero no queremos que aparezcan en el menú.
# Se usarán en el futuro como inlines específicos si los activamos.
class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 0
    fields = ("category", "subcategory", "description", "hours_spent", "is_external", "labor_rate")
    autocomplete_fields = ("category", "subcategory")
    verbose_name = "Trabajo adicional"
    verbose_name_plural = "Trabajos adicionales"


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 0
    fields = ("part", "quantity", "cost_at_moment")
    autocomplete_fields = ("part",)
    verbose_name = "Repuesto usado"
    verbose_name_plural = "Repuestos usados"


# ---------------------------
# Admin de OT
# ---------------------------

class WorkOrderAdminForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Renombrar dinámicamente etiqueta sin tocar el modelo (evita migraciones)
        if "assigned_technician" in self.fields:
            self.fields["assigned_technician"].label = "Gestor asignado"

        # Placeholders útiles
        if "description" in self.fields:
            self.fields["description"].widget.attrs.setdefault(
                "placeholder",
                "Describe el problema o la intervención principal…",
            )
        if "pre_diagnosis" in self.fields:
            self.fields["pre_diagnosis"].widget.attrs.setdefault(
                "placeholder",
                "Pre-diagnóstico (si aplica para correctivo)…",
            )


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    form = WorkOrderAdminForm

    # Vista de lista
    list_display = (
        "id",
        "order_type",
        "vehicle",
        "status",
        "priority",
        "gestor_asignado",
        "created_at",
        "out_of_service",
        "requires_approval",
    )
    list_filter = (
        "order_type",
        "status",
        "priority",
        "out_of_service",
        "requires_approval",
        "severity",
    )
    search_fields = (
        "id",
        "vehicle__plate",
        "description",
        "pre_diagnosis",
        "notes__text",
        "drivers__full_name",
        "drivers__document_number",
    )
    date_hierarchy = "created_at"
    autocomplete_fields = ("vehicle", "assigned_technician", "probable_causes")

    # Secciones del formulario (agrupadas y claras)
    fieldsets = (
        (_("Datos generales"), {
            "fields": (
                "order_type",
                "vehicle",
                "status",
                "priority",
                "assigned_technician",
                "description",
            )
        }),
        (_("Planificación y tiempos"), {
            "classes": ("collapse",),
            "fields": (
                "scheduled_start", "scheduled_end",
                "check_in_at", "check_out_at",
                "odometer_at_service",
            )
        }),
        (_("Diagnóstico (Correctivo)"), {
            "classes": ("collapse",),
            "fields": (
                "pre_diagnosis",
                "failure_origin",
                "severity",
                "warranty_covered",
                "requires_approval",
                "out_of_service",
                "probable_causes",
            )
        }),
        (_("Costos (solo lectura, se recalculan)"), {
            "classes": ("collapse",),
            "fields": ("labor_cost_internal", "labor_cost_external", "parts_cost")
        }),
        (_("Trazabilidad"), {
            "classes": ("collapse",),
            "fields": ("created_at",)
        }),
    )

    readonly_fields = ("created_at", "labor_cost_internal", "labor_cost_external", "parts_cost")

    # Inlines activos (Conductores, Novedades, Adjuntos)
    inlines = (
        WorkOrderDriverInline,
        WorkOrderNoteInline,
        WorkOrderAttachmentInline,
        # Dejamos preparados pero desactivados para no sobrecargar formulario:
        # WorkOrderTaskInline,
        # WorkOrderPartInline,
    )

    def gestor_asignado(self, obj: WorkOrder):
        user = getattr(obj, "assigned_technician", None)
        if not user:
            return "—"
        # Muestra nombre + username para claridad
        return f"{getattr(user, 'get_full_name', lambda: str(user))() or user.username} (@{user.username})"
    gestor_asignado.short_description = "Gestor asignado"


# ---------------------------
# (Opcional) Quitar del menú “Trabajos adicionales” y “Repuestos usados”
# ---------------------------
# Están registrados solo como inlines en OT, no como modelos de menú.
try:
    admin.site.unregister(WorkOrderTask)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(WorkOrderPart)
except admin.sites.NotRegistered:
    pass
