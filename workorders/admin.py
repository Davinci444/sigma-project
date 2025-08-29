"""Admin de órdenes de trabajo y planes de mantenimiento (SIGMA)."""

from django import forms
from django.contrib import admin, messages

from .models import (
    MaintenancePlan,
    WorkOrder,
    WorkOrderTask,
    WorkOrderPart,
    MaintenanceCategory,
    MaintenanceSubcategory,
    MaintenanceManual,
    ManualTask,
)
from .corrective_models import (
    WorkOrderCorrective,
    WorkOrderDriverAssignment,
)
from users.models import Driver


# ==========================
# Formulario con JS dependiente (Categoría -> Subcategoría)
# ==========================

class WorkOrderTaskForm(forms.ModelForm):
    class Meta:
        model = WorkOrderTask
        fields = "__all__"

    class Media:
        js = ("workorders/js/admin_dependent_subcategory.js",)


# ==========================
# Inlines existentes (tareas, repuestos)
# ==========================

class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    form = WorkOrderTaskForm
    extra = 1
    autocomplete_fields = ("category", "subcategory")
    fields = ("category", "subcategory", "description", "estimated_hours", "actual_hours", "is_completed")


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1
    autocomplete_fields = ("part",)
    fields = ("part", "quantity", "unit_cost")


# ==========================
# Inlines Correctivo (nuevo)
# ==========================

class WorkOrderCorrectiveInline(admin.StackedInline):
    model = WorkOrderCorrective
    extra = 0
    max_num = 1
    can_delete = True
    fields = ("pre_diagnosis",)


class WorkOrderDriverAssignmentInline(admin.TabularInline):
    model = WorkOrderDriverAssignment
    extra = 1
    autocomplete_fields = ("driver",)
    fields = ("driver", "role", "notes")

    _parent_obj = None

    def get_formset(self, request, obj=None, **kwargs):
        # Guardamos la OT padre para filtrar por zona del vehículo
        self._parent_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filtrar conductores por Zona del vehículo (si existe)
        if db_field.name == "driver":
            qs = Driver.objects.filter(active=True)
            zone = None
            if self._parent_obj and getattr(self._parent_obj, "vehicle_id", None):
                zone = getattr(getattr(self._parent_obj, "vehicle", None), "zone", None)
            if zone:
                qs = qs.filter(zone=zone)
            kwargs["queryset"] = qs.order_by("full_name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==========================
# Catálogos / Manuales
# ==========================

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


# ==========================
# Planes
# ==========================

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle", "manual", "is_active", "last_service_km", "last_service_date")
    list_filter = ("is_active", "manual")
    search_fields = ("vehicle__plate", "manual__name")
    # Usar raw_id_fields para evitar dependencias de autocomplete en admins externos
    raw_id_fields = ("vehicle", "manual")
    list_select_related = ("vehicle", "manual")
    date_hierarchy = "last_service_date"


# ==========================
# Órdenes de Trabajo
# ==========================

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    """
    Admin de OT con:
    - Inlines de tareas, repuestos
    - Inlines de correctivo (pre-diagnóstico y conductores) SOLO en edición y si la OT es CORRECTIVE
    - Advertencia de preventivo vencido al abrir OT preventiva
    """
    list_display = (
        "id", "order_type", "status", "vehicle", "priority",
        "scheduled_start", "scheduled_end", "created_at",
    )
    list_filter = ("order_type", "status", "priority")
    search_fields = ("id", "vehicle__plate", "vehicle__brand", "vehicle__model")
    autocomplete_fields = ("vehicle",)
    date_hierarchy = "scheduled_start"
    list_select_related = ("vehicle",)

    # Definimos todos, pero los filtramos dinámicamente en get_inline_instances
    inlines = [WorkOrderTaskInline, WorkOrderPartInline, WorkOrderCorrectiveInline, WorkOrderDriverAssignmentInline]

    fieldsets = (
        ("Información básica", {
            "fields": ("order_type", "status", "vehicle", "priority", "description")
        }),
        ("Programación", {
            "fields": ("scheduled_start", "scheduled_end")
        }),
        ("Ejecución", {
            "fields": ("check_in_at", "check_out_at")
        }),
        ("Meta", {
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)

    def get_inline_instances(self, request, obj=None):
        """
        - En CREACIÓN (obj is None): mostrar SOLO tareas y repuestos.
        - En EDICIÓN: si la OT es CORRECTIVE, mostrar además correctivo y conductores.
        """
        instances = super().get_inline_instances(request, obj)
        filtered = []
        for inst in instances:
            is_corrective_inline = isinstance(inst, (WorkOrderCorrectiveInline, WorkOrderDriverAssignmentInline))
            if obj is None:
                # En "Add" ocultar los inlines de correctivo
                if is_corrective_inline:
                    continue
            else:
                # En "Change": solo mostrar correctivo si la OT es correctiva
                if is_corrective_inline and obj.order_type != WorkOrder.OrderType.CORRECTIVE:
                    continue
            filtered.append(inst)
        return filtered

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        """
        Si es PREVENTIVA y el plan está vencido según el manual, mostrar advertencia.
        """
        if obj and obj.order_type == WorkOrder.OrderType.PREVENTIVE and obj.vehicle:
            vehicle = obj.vehicle
            plan = (
                MaintenancePlan.objects.filter(vehicle=vehicle, is_active=True)
                .select_related("manual")
                .first()
            )
            if plan and plan.manual:
                tasks_qs = plan.manual.tasks.order_by("km_interval")
                base_km = plan.last_service_km or 0
                current = vehicle.current_odometer_km or 0
                delta = max(0, current - base_km)

                next_task = None
                for t in tasks_qs:
                    if t.km_interval >= delta:
                        next_task = t
                        break
                if not next_task:
                    first = plan.manual.tasks.order_by("km_interval").first()
                    period = (first.km_interval if first and first.km_interval else 10000)
                    next_due_km = base_km + ((delta // period) + 1) * period
                    desc = f"Ciclo cada {period} km"
                else:
                    next_due_km = base_km + next_task.km_interval
                    desc = next_task.description

                if current >= next_due_km:
                    mensaje = f"¡Mantenimiento Preventivo VENCIDO! Próximo servicio ({desc}) era a los {next_due_km} km."
                    messages.warning(request, f"ATENCIÓN: {mensaje}")

        return super().render_change_form(request, context, add, change, form_url, obj)
