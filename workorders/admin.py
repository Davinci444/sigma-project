"""Admin de Órdenes de Trabajo: UX diferenciada, evidencias integradas en la misma pantalla con “paracaídas” para evitar 500 en /add/."""

from django.contrib import admin, messages
from django.utils.html import format_html
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.template import loader, TemplateDoesNotExist
from django.db.models import Q
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
    WorkOrderTaskEvidence,  # <- evidencia por trabajo (file upload)
)

# ---------------------------------------------------------------------
# Roles (por grupo; sin migraciones)
# ---------------------------------------------------------------------

GERENCIA_GROUP_NAME = "Gerencia"
COORDINACION_GROUP_NAME = "Coordinación de Zona"

def es_gerencia(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=GERENCIA_GROUP_NAME).exists()

def es_coordinacion(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=COORDINACION_GROUP_NAME).exists()


# ---------------------------------------------------------------------
# FORM principal de OT (validación sin tocar modelos)
# ---------------------------------------------------------------------

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
            cleaned["pre_diagnosis"] = ""
            cleaned["failure_origin"] = None
            cleaned["severity"] = None
            cleaned["requires_approval"] = False
            cleaned["out_of_service"] = False
            cleaned["warranty_covered"] = False
            cleaned["probable_causes"] = []

        return cleaned


# ---------------------------------------------------------------------
# FORM rápido para subir evidencias dentro de la pantalla de la OT
# ---------------------------------------------------------------------

class WorkOrderEvidenceQuickForm(forms.ModelForm):
    class Meta:
        model = WorkOrderTaskEvidence
        fields = ("task", "file", "description")

    def __init__(self, *args, **kwargs):
        self.work_order = kwargs.pop("work_order", None)
        super().__init__(*args, **kwargs)
        if self.work_order is not None:
            self.fields["task"].queryset = WorkOrderTask.objects.filter(
                work_order=self.work_order
            ).select_related("work_order")
        self.fields["task"].label = "Trabajo asociado"
        self.fields["file"].label = "Archivo (imagen/video/pdf, etc.)"
        self.fields["description"].label = "Descripción (opcional)"


# ---------------------------------------------------------------------
# INLINES
# ---------------------------------------------------------------------

class WorkOrderDriverInline(admin.TabularInline):
    model = WorkOrderDriver
    extra = 0
    autocomplete_fields = ["driver"]
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if es_gerencia(request.user):
            return qs
        return qs.filter(visibility=WorkOrderNote.Visibility.ALL)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "visibility" and not es_gerencia(request.user):
            kwargs["choices"] = [
                (WorkOrderNote.Visibility.ALL, "Todos"),
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 0
    autocomplete_fields = ("category", "subcategory")
    fields = (
        "category",
        "subcategory",
        "description",
        "hours_spent",
        "is_external",
        "labor_rate",
    )
    verbose_name = "Trabajo"
    verbose_name_plural = "Trabajos"


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 0
    autocomplete_fields = ("part",)
    fields = ("part", "quantity", "cost_at_moment")
    verbose_name = "Repuesto usado"
    verbose_name_plural = "Repuestos usados"


# ---------------------------------------------------------------------
# Filtro y Acciones
# ---------------------------------------------------------------------

class InWorkshopFilter(admin.SimpleListFilter):
    title = "¿En taller?"
    parameter_name = "in_workshop"

    def lookups(self, request, model_admin):
        return (("yes", "Sí"), ("no", "No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                Q(check_in_at__isnull=False)
                & ~Q(status__in=[
                    WorkOrder.OrderStatus.VERIFIED,
                    WorkOrder.OrderStatus.CANCELLED,
                    WorkOrder.OrderStatus.COMPLETED,
                ])
            )
        if self.value() == "no":
            return queryset.filter(
                Q(check_in_at__isnull=True)
                | Q(status__in=[
                    WorkOrder.OrderStatus.VERIFIED,
                    WorkOrder.OrderStatus.CANCELLED,
                    WorkOrder.OrderStatus.COMPLETED,
                ])
            )
        return queryset


def exportar_ot_csv(modeladmin, request, queryset):
    filename = f"ordenes_trabajo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(resp)

    writer.writerow([
        "ID", "Placa", "Tipo", "Estado", "Prioridad", "Severidad",
        "Gestor", "Programado_Inicio", "Programado_Fin",
        "Ingreso", "Salida", "KM_Atencion", "Costo_MO_Int", "Costo_MO_Ext",
        "Costo_Repuestos", "Fecha_Creacion"
    ])

    for obj in queryset.select_related("vehicle", "assigned_technician"):
        gestor = ""
        if obj.assigned_technician:
            full = getattr(obj.assigned_technician, "get_full_name", lambda: "")() or ""
            gestor = full or getattr(obj.assigned_technician, "username", "") or str(obj.assigned_technician)

        writer.writerow([
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


def marcar_en_recepcion(modeladmin, request, queryset):
    updated = queryset.update(status=WorkOrder.OrderStatus.IN_RECEPTION)
    messages.success(request, f"{updated} OT(s) marcadas En Recepción.")
marcar_en_recepcion.short_description = "Marcar como En Recepción"

def marcar_en_servicio(modeladmin, request, queryset):
    updated = queryset.update(status=WorkOrder.OrderStatus.IN_SERVICE)
    messages.success(request, f"{updated} OT(s) marcadas En Servicio.")
marcar_en_servicio.short_description = "Marcar como En Servicio"

def marcar_completada(modeladmin, request, queryset):
    updated = queryset.update(status=WorkOrder.OrderStatus.COMPLETED)
    messages.success(request, f"{updated} OT(s) marcadas Completadas.")
marcar_completada.short_description = "Marcar como Completada"

def marcar_verificada(modeladmin, request, queryset):
    updated = queryset.update(status=WorkOrder.OrderStatus.VERIFIED)
    messages.success(request, f"{updated} OT(s) marcadas Verificadas.")
marcar_verificada.short_description = "Marcar como Verificada"


# ---------------------------------------------------------------------
# ADMIN WorkOrder
# ---------------------------------------------------------------------

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    form = WorkOrderAdminForm
    actions = [
        exportar_ot_csv,
        marcar_en_recepcion,
        marcar_en_servicio,
        marcar_completada,
        marcar_verificada,
    ]

    list_display = (
        "id",
        "vehicle_plate",
        "order_type",
        "status_badge",
        "priority",
        "severity",
        "assigned_technician_name",
        "created_at",
    )
    list_select_related = ("vehicle", "assigned_technician")
    list_filter = (
        "order_type",
        "status",
        "priority",
        "severity",
        "failure_origin",
        "out_of_service",
        "warranty_covered",
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

    # -------- Helpers de columnas --------
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
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Estado"

    # -------- Fieldsets para toggle Preventivo/Correctivo --------
    BASE_FIELDS = (
        ("Información básica", {
            "classes": ("sigma-base",),
            "fields": (
                "order_type",
                "vehicle",
                "description",
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

    def get_readonly_fields(self, request, obj=None):
        return ("created_at",)

    def get_exclude(self, request, obj=None):
        ot = self._order_type_from_request(request, obj)
        if ot == WorkOrder.OrderType.PREVENTIVE:
            return ("pre_diagnosis", "failure_origin", "severity", "out_of_service",
                    "requires_approval", "warranty_covered", "probable_causes")
        return ()

    class Media:
        js = ("workorders/admin_workorder.js",)

    # -------- URLs extra para borrar evidencia --------
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<path:object_id>/delete-evidence/<int:evid_id>/",
                self.admin_site.admin_view(self.delete_evidence),
                name="workorders_workorder_delete_evidence",
            ),
        ]
        return my_urls + urls

    def delete_evidence(self, request, object_id, evid_id):
        obj = self.get_object(request, object_id)
        if obj is None:
            messages.error(request, "OT no encontrada.")
            return HttpResponseRedirect(reverse("admin:workorders_workorder_changelist"))

        ev = WorkOrderTaskEvidence.objects.filter(
            pk=evid_id, task__work_order=obj
        ).first()
        if not ev:
            messages.error(request, "Evidencia no encontrada o no pertenece a esta OT.")
        else:
            ev.delete()
            messages.success(request, "Evidencia eliminada.")

        return HttpResponseRedirect(reverse("admin:workorders_workorder_change", args=[object_id]))

    # -------- Vista de change con “paracaídas” --------
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """
        - En /add/ (object_id=None): devolvemos la vista estándar del admin (NO plantilla custom). -> Anti-500.
        - En /change/: intentamos cargar plantilla custom. Si no existe, mostramos estándar (Anti-500).
        """
        # /add/ -> sin plantilla custom
        if not object_id:
            return super().changeform_view(request, object_id, form_url, extra_context)

        # /change/ -> primero ejecutamos la vista base
        response = super().changeform_view(request, object_id, form_url, extra_context)
        if isinstance(response, HttpResponseRedirect):
            return response

        # Intentamos obtener el objeto
        obj = WorkOrder.objects.filter(pk=object_id).first()
        if not obj:
            return response  # Fallback seguro

        # Si se envió el mini-form de evidencias
        if request.method == "POST" and "_upload_evidence" in request.POST:
            form = WorkOrderEvidenceQuickForm(
                request.POST, request.FILES, work_order=obj
            )
            if form.is_valid():
                form.save()
                messages.success(request, "Evidencia cargada correctamente.")
                return HttpResponseRedirect(
                    reverse("admin:workorders_workorder_change", args=[object_id])
                )
            else:
                messages.error(request, "Revisa el formulario de evidencia.")

        # Construimos contexto
        quick_form = WorkOrderEvidenceQuickForm(work_order=obj)
        tasks = (
            WorkOrderTask.objects.filter(work_order=obj)
            .select_related("work_order", "category", "subcategory")
            .order_by("id")
        )
        evidences_by_task = (
            WorkOrderTaskEvidence.objects.filter(task__work_order=obj)
            .select_related("task")
            .order_by("-uploaded_at")
        )
        mapping = {t.id: {"task": t, "evidences": []} for t in tasks}
        for ev in evidences_by_task:
            mapping.get(ev.task_id, {"task": None, "evidences": []})["evidences"].append(ev)
        evidence_groups = [mapping[k] for k in mapping]

        ctx = response.context_data if hasattr(response, "context_data") else {}
        ctx = ctx or {}
        ctx["sigma_quick_evidence_form"] = quick_form
        ctx["sigma_evidence_groups"] = evidence_groups

        # Si la plantilla custom no existe, caemos al template estándar del admin (sin romper).
        try:
            loader.get_template("admin/workorders/workorder/change_form.html")
        except TemplateDoesNotExist:
            return TemplateResponse(
                request,
                self.change_form_template or "admin/change_form.html",
                ctx,
            )

        return TemplateResponse(
            request,
            "admin/workorders/workorder/change_form.html",
            ctx,
        )


# ---------------------------------------------------------------------
# Otros modelos
# ---------------------------------------------------------------------

@admin.register(WorkOrderTask)
class WorkOrderTaskAdmin(admin.ModelAdmin):
    list_display = ("__str__", "work_order", "category", "subcategory", "hours_spent", "is_external", "evidencias_btn")
    search_fields = ("description", "work_order__id", "work_order__vehicle__plate")
    list_filter = ("is_external", "category", "subcategory")
    autocomplete_fields = ("work_order", "category", "subcategory")

    def evidencias_btn(self, obj):
        return format_html(
            '<a class="button" href="/admin/workorders/workordertaskevidence/?task__id__exact={}">Ver evidencias</a>',
            obj.pk
        )
    evidencias_btn.short_description = "Evidencias"


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


@admin.register(WorkOrderPart)
class WorkOrderPartAdmin(admin.ModelAdmin):
    autocomplete_fields = ("work_order", "part")
    list_display = ("work_order", "part", "quantity", "cost_at_moment")
    search_fields = ("work_order__vehicle__plate", "part__name")
    list_filter = ("part",)


@admin.register(WorkOrderAttachment)
class WorkOrderAttachmentAdmin(admin.ModelAdmin):
    autocomplete_fields = ("work_order",)
    list_display = ("work_order", "url", "created_at")
    search_fields = ("work_order__vehicle__plate", "url")
    date_hierarchy = "created_at"


@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    autocomplete_fields = ("work_order", "author")
    list_display = ("work_order", "visibility", "short_text", "author", "created_at")
    search_fields = ("work_order__vehicle__plate", "text")
    list_filter = ("visibility",)
    date_hierarchy = "created_at"

    def short_text(self, obj):
        return (obj.text[:70] + "…") if len(obj.text) > 70 else obj.text
    short_text.short_description = "Comentario"


@admin.register(WorkOrderDriver)
class WorkOrderDriverAdmin(admin.ModelAdmin):
    autocomplete_fields = ("work_order", "driver")
    list_display = ("work_order", "driver", "responsibility_percent")
    search_fields = ("work_order__vehicle__plate", "driver__full_name")


@admin.register(WorkOrderTaskEvidence)
class WorkOrderTaskEvidenceAdmin(admin.ModelAdmin):
    list_display = ("task", "file", "uploaded_at", "mini")
    list_select_related = ("task", "task__work_order")
    search_fields = ("task__description", "task__work_order__vehicle__plate")
    date_hierarchy = "uploaded_at"
    autocomplete_fields = ("task",)

    def mini(self, obj):
        if not obj.file:
            return "—"
        name = (obj.file.name or "").lower()
        if name.endswith((".jpg", ".jpeg", ".png", ".gif")):
            return format_html('<img src="{}" style="max-height:50px;border:1px solid #ccc;" />', obj.file.url)
        if name.endswith((".mp4", ".mov", ".avi", ".webm")):
            return "🎬"
        return "📎"
    mini.short_description = "Preview"
