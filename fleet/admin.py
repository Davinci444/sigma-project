"""Admin de Vehículos con inline de repuestos por vehículo."""
from django.contrib import admin
from django.db.models import Q
from django.urls import path
from django.http import JsonResponse, HttpRequest

from .models import Vehicle
from workorders.models import WorkOrder
from inventory.models import SpareCategory, SpareItem, VehicleSpare

IN_WORKSHOP_STATUSES = [
    WorkOrder.OrderStatus.IN_PROGRESS,
    WorkOrder.OrderStatus.WAITING_PART,
    WorkOrder.OrderStatus.IN_ROAD_TEST,
]


class EnTallerFilter(admin.SimpleListFilter):
    title = "¿Vehículo en taller?"
    parameter_name = "in_workshop"

    def lookups(self, request, model_admin):
        return (("yes", "Sí"), ("no", "No"))

    def queryset(self, request, qs):
        if self.value() == "yes":
            return qs.filter(
                workorder__check_in_at__isnull=False,
                workorder__status__in=IN_WORKSHOP_STATUSES,
            ).distinct()
        if self.value() == "no":
            return qs.exclude(
                Q(
                    workorder__check_in_at__isnull=False,
                    workorder__status__in=IN_WORKSHOP_STATUSES,
                )
            ).distinct()
        return qs


class VehicleSpareInline(admin.TabularInline):
    model = VehicleSpare
    extra = 1
    fields = ("category", "spare_item", "brand", "part_number", "quantity",
              "last_replacement_date", "next_replacement_km", "notes")
    autocomplete_fields = ("spare_item",)

    def get_fields(self, request, obj=None):
        fs = list(super().get_fields(request, obj))
        if "category" not in fs:
            fs.insert(0, "category")
        return fs

    def formfield_for_dbfield(self, db_field, **kwargs):
        from django import forms
        if db_field.name == "category":
            return forms.ModelChoiceField(
                queryset=SpareCategory.objects.filter(is_active=True).order_by("name"),
                required=False,
                label="Categoría",
            )
        return super().formfield_for_dbfield(db_field, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spare_item":
            cat_id = request.POST.get("category") or request.GET.get("category")
            if cat_id:
                kwargs["queryset"] = SpareItem.objects.filter(category_id=cat_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate", "vehicle_type", "fuel_type", "current_odometer_km",
        "usuario_gestor_asignado", "en_taller",
    )
    list_filter = ("vehicle_type", "fuel_type", EnTallerFilter)
    search_fields = ("plate", "vin", "brand", "linea", "modelo")
    ordering = ("plate",)

    inlines = [VehicleSpareInline]

    class Media:
        js = ("fleet/admin_vehicle_spares.js",)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("spare-items/", self.admin_site.admin_view(self.spare_items_view), name="vehicle_spare_items"),
        ]
        return custom + urls

    def spare_items_view(self, request: HttpRequest):
        cat_id = request.GET.get("category")
        qs = SpareItem.objects.all()
        if cat_id:
            qs = qs.filter(Q(category_id=cat_id))
        data = [{"id": it.pk, "text": it.name} for it in qs.order_by("name")[:500]]
        return JsonResponse(data, safe=False)

    # helpers
    def usuario_gestor_asignado(self, obj: Vehicle):
        for name in ("assigned_user", "user", "owner", "manager", "assigned_to"):
            if hasattr(obj, name):
                u = getattr(obj, name)
                if u:
                    full = getattr(u, "get_full_name", lambda: "")() or ""
                    return full or getattr(u, "username", None) or str(u)
        return "—"
    usuario_gestor_asignado.short_description = "Usuario / Gestor"

    def en_taller(self, obj: Vehicle) -> bool:
        return WorkOrder.objects.filter(
            vehicle=obj,
            check_in_at__isnull=False,
            status__in=IN_WORKSHOP_STATUSES,
        ).exists()
    en_taller.boolean = True
    en_taller.short_description = "En taller"
