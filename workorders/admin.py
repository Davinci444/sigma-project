"""Admin MINIMAL-ULTRA para aislar el 500 en 'Añadir OT'."""

from django.contrib import admin
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

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    fields = (
        "order_type",
        "vehicle",
        "description",
        "priority",
        "status",
        "created_at",
    )
    readonly_fields = ("created_at",)
    raw_id_fields = ("vehicle",)
    list_display = ("id", "vehicle", "order_type", "status", "priority", "created_at")
    list_select_related = ("vehicle",)
    search_fields = ("id", "vehicle__plate", "description")
    list_filter = ("order_type", "status", "priority")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)

@admin.register(MaintenanceSubcategory)
class MaintenanceSubcategoryAdmin(admin.ModelAdmin):
    raw_id_fields = ("category",)
    list_display = ("name", "category")
    search_fields = ("name", "category__name")

@admin.register(MaintenanceManual)
class MaintenanceManualAdmin(admin.ModelAdmin):
    list_display = ("name", "fuel_type")
    list_filter = ("fuel_type",)
    search_fields = ("name",)

@admin.register(ManualTask)
class ManualTaskAdmin(admin.ModelAdmin):
    raw_id_fields = ("manual",)
    list_display = ("manual", "km_interval", "description")
    list_filter = ("manual",)
    search_fields = ("description",)

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    raw_id_fields = ("vehicle", "manual")
    list_display = ("vehicle", "manual", "is_active", "last_service_km", "last_service_date")
    list_filter = ("is_active", "manual__fuel_type")
    search_fields = ("vehicle__plate",)

@admin.register(ProbableCause)
class ProbableCauseAdmin(admin.ModelAdmin):
    search_fields = ("name", "description")
    list_display = ("name",)

@admin.register(WorkOrderTask)
class WorkOrderTaskAdmin(admin.ModelAdmin):
    raw_id_fields = ("work_order", "category", "subcategory")
    list_display = ("work_order", "category", "subcategory", "hours_spent", "is_external")

@admin.register(WorkOrderPart)
class WorkOrderPartAdmin(admin.ModelAdmin):
    raw_id_fields = ("work_order", "part")
    list_display = ("work_order", "part", "quantity", "cost_at_moment")

@admin.register(WorkOrderAttachment)
class WorkOrderAttachmentAdmin(admin.ModelAdmin):
    raw_id_fields = ("work_order",)
    list_display = ("work_order", "url", "description", "created_at")
    readonly_fields = ("created_at",)

@admin.register(WorkOrderNote)
class WorkOrderNoteAdmin(admin.ModelAdmin):
    raw_id_fields = ("work_order", "author")
    list_display = ("work_order", "visibility", "author", "created_at")
    readonly_fields = ("created_at",)

@admin.register(WorkOrderDriver)
class WorkOrderDriverAdmin(admin.ModelAdmin):
    raw_id_fields = ("work_order", "driver")
    list_display = ("work_order", "driver", "responsibility_percent")
