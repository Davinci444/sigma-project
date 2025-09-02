"""Admin de Vehículos con inline de repuestos por vehículo."""
from django import forms
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


class VehicleSpareForm(forms.ModelForm):
    """Form used in the inline to dynamically pick spare items by category."""

    category = forms.ModelChoiceField(
        queryset=SpareCategory.objects.filter(is_active=True).order_by("name"),
        required=False,
        label="Categoría",
    )

    class Meta:
        model = VehicleSpare
        fields = (
            "category",
            "spare_item",
            "brand",
            "part_number",
            "quantity",
            "last_replacement_date",
            "next_replacement_km",
            "notes",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Determine current category either from POST data or existing instance
        cat_id = self.data.get("category") or self.initial.get("category")
        if not cat_id and self.instance.pk and self.instance.spare_item:
            cat_id = self.instance.spare_item.category_id
            self.fields["category"].initial = self.instance.spare_item.category

        if cat_id:
            try:
                self.fields["spare_item"].queryset = SpareItem.objects.filter(
                    category_id=cat_id
                )
            except (ValueError, TypeError):
                self.fields["spare_item"].queryset = SpareItem.objects.none()
        else:
            # Avoid loading all items when category hasn't been chosen
            self.fields["spare_item"].queryset = SpareItem.objects.none()


class VehicleSpareInline(admin.TabularInline):
    model = VehicleSpare
    form = VehicleSpareForm
    extra = 1
    fields = (
        "category",
        "spare_item",
        "brand",
        "part_number",
        "quantity",
        "last_replacement_date",
        "next_replacement_km",
        "notes",
    )


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
