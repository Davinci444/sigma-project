# workorders/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import FieldDoesNotExist
from django.apps import apps
from django.urls import reverse_lazy

from .models import (
    WorkOrder, WorkOrderTask, WorkOrderNote, ProbableCause
)

# -------- Utilidades seguras --------
def _field_exists(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False

def _model_or_none(app_label: str, model_name: str):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None

# Intenta resolver modelos externos (si no existen, ocultamos sus secciones)
Driver = _model_or_none("users", "Driver")
Vehicle = _model_or_none("fleet", "Vehicle")
TaskCategory = _model_or_none("workorders", "TaskCategory")
TaskSubcategory = _model_or_none("workorders", "TaskSubcategory")
WorkOrderDriver = _model_or_none("workorders", "WorkOrderDriver")

# Choices seguros por si el modelo no define enums
SeverityEnum = getattr(WorkOrder, "Severity", None)
FailureOriginEnum = getattr(WorkOrder, "FailureOrigin", None)
SEVERITY_CHOICES = getattr(SeverityEnum, "choices", [])
FAILURE_ORIGIN_CHOICES = getattr(FailureOriginEnum, "choices", [])
if not SEVERITY_CHOICES:
    SEVERITY_CHOICES = [("","---------"), ("LOW","Baja"), ("MEDIUM","Media"), ("HIGH","Alta")]
if not FAILURE_ORIGIN_CHOICES:
    FAILURE_ORIGIN_CHOICES = [("","---------"), ("MECHANICAL","Mecánica"), ("ELECTRICAL","Eléctrica"), ("OTHER","Otra")]

# ---------- Form principal unificado ----------
class WorkOrderUnifiedForm(forms.ModelForm):
    # Conductor y % de responsabilidad (solo si hay modelo Driver)
    if Driver:
        driver = forms.ModelChoiceField(
            label="Conductor responsable",
            queryset=getattr(Driver, "objects", Driver) if hasattr(Driver, "objects") else [],
            required=False,
            widget=forms.Select(
                attrs={
                    "class": "select2-ajax",
                    "data-url": reverse_lazy("driver-list"),
                }
            ),
        )
        driver_responsibility = forms.DecimalField(
            label="Responsabilidad del conductor (%)",
            required=False, min_value=0, max_value=100
        )

    # Correctivo (UI decide mostrar)
    pre_diagnosis = forms.CharField(
        label="Pre-diagnóstico (solo correctivo)",
        required=False, widget=forms.Textarea(attrs={'rows':3})
    )
    failure_origin = forms.ChoiceField(
        label="Origen de la falla (solo correctivo)",
        choices=FAILURE_ORIGIN_CHOICES, required=False
    )
    severity = forms.ChoiceField(
        label="Severidad (solo correctivo)",
        choices=SEVERITY_CHOICES, required=False
    )

    # Novedades rápidas
    first_comment = forms.CharField(
        label="Comentario inicial (opcional)",
        required=False, widget=forms.Textarea(attrs={'rows':2})
    )
    probable_causes = forms.ModelMultipleChoiceField(
        label="Causas probables (opcional, solo correctivo)",
        queryset=ProbableCause.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    # Campos datetime “reales” si existen en tu modelo
    dynamic_datetime_fields = ("actual_start", "actual_end", "received_at", "delivered_at", "started_at", "finished_at")

    class Meta:
        model = WorkOrder
        fields = [
            'order_type', 'vehicle', 'description',
            'status', 'priority',
            'scheduled_start', 'scheduled_end',
            'odometer_at_service',
            # Campos de costo general si tu modelo los trae (se añaden abajo dinámicamente)
        ]
        widgets = {
            'vehicle': forms.Select(
                attrs={'class': 'select2-ajax', 'data-url': reverse_lazy('vehicle-list')}
            ),
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializar conductor existente
        if (
            Driver
            and WorkOrderDriver
            and self.instance
            and getattr(self.instance, "pk", None)
            and 'driver' in self.fields
            and 'driver_responsibility' in self.fields
        ):
            try:
                wod = (
                    WorkOrderDriver.objects
                    .filter(work_order=self.instance)
                    .select_related('driver')
                    .first()
                )
                if wod:
                    self.fields['driver'].initial = getattr(wod, 'driver', None)
                    self.fields['driver_responsibility'].initial = getattr(
                        wod,
                        'responsibility_percent',
                        None,
                    )
            except Exception:
                pass

        # Campos datetime reales si existen
        for fname in self.dynamic_datetime_fields:
            if _field_exists(WorkOrder, fname):
                self.fields[fname] = forms.DateTimeField(
                    required=False,
                    widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                    label=fname.replace("_", " ").capitalize()
                )

        # Campos de costo general (si existen en tu WorkOrder)
        for fname in ("is_external", "external_vendor", "external_cost", "service_cost", "total_cost"):
            if _field_exists(WorkOrder, fname) and fname not in self.fields:
                self.fields[fname] = forms.CharField(
                    required=False,
                    label=fname.replace("_", " ").capitalize()
                )
                # Si es bool o decimal, mejoramos el widget:
                try:
                    fobj = WorkOrder._meta.get_field(fname)
                    from django.db import models
                    if isinstance(fobj, models.BooleanField):
                        self.fields[fname] = forms.BooleanField(required=False, label=fobj.verbose_name or "¿Externo?")
                    elif isinstance(fobj, (models.DecimalField, models.FloatField, models.IntegerField)):
                        self.fields[fname] = forms.DecimalField(required=False, label=fobj.verbose_name or fname.replace("_"," ").capitalize())
                except Exception:
                    pass

    def save(self, user=None, commit=True):
        instance = super().save(commit=commit)

        # Conductor / responsabilidad (sólo si existen modelos)
        if Driver and WorkOrderDriver and 'driver' in self.cleaned_data:
            driver = self.cleaned_data.get('driver')
            resp = self.cleaned_data.get('driver_responsibility')
            if driver:
                WorkOrderDriver.objects.update_or_create(
                    work_order=instance, driver=driver,
                    defaults={'responsibility_percent': resp}
                )
            else:
                WorkOrderDriver.objects.filter(work_order=instance).delete()

        # Comentario inicial -> WorkOrderNote
        comment = self.cleaned_data.get('first_comment')
        if comment:
            note = WorkOrderNote(text=comment, work_order=instance)
            if _field_exists(WorkOrderNote, "author") and user is not None:
                setattr(note, "author", user)
            note.save()

        causas = self.cleaned_data.get('probable_causes')
        ot_val = str(self.cleaned_data.get('order_type')).upper()
        ot_is_corrective = ("CORRECTIVE" in ot_val or "CORRECTIV" in ot_val)
        if ot_is_corrective:
            instance.probable_causes.set(causas or [])
        else:
            instance.probable_causes.clear()

        # Guardar campos correctivo si existen en el modelo
        if ot_is_corrective:
            if _field_exists(WorkOrder, "pre_diagnosis"):
                instance.pre_diagnosis = self.cleaned_data.get('pre_diagnosis')
            if _field_exists(WorkOrder, "failure_origin"):
                instance.failure_origin = self.cleaned_data.get('failure_origin') or getattr(instance, "failure_origin", None)
            if _field_exists(WorkOrder, "severity"):
                instance.severity = self.cleaned_data.get('severity') or getattr(instance, "severity", None)
            instance.save()
        else:
            if _field_exists(WorkOrder, "pre_diagnosis"):
                instance.pre_diagnosis = ""
            if _field_exists(WorkOrder, "failure_origin"):
                instance.failure_origin = None
            if _field_exists(WorkOrder, "severity"):
                instance.severity = None
            instance.save()

        # Guardar campos datetime reales, si existen
        touched_dt = False
        for fname in self.dynamic_datetime_fields:
            if fname in self.fields:
                setattr(instance, fname, self.cleaned_data.get(fname))
                touched_dt = True
        if touched_dt:
            instance.save()

        # Guardar campos de costo general si existen
        for fname in ("is_external", "external_vendor", "external_cost", "service_cost", "total_cost"):
            if fname in self.fields:
                val = self.cleaned_data.get(fname)
                try:
                    setattr(instance, fname, val)
                except Exception:
                    pass
        if any(f in self.fields for f in ("is_external","external_vendor","external_cost","service_cost","total_cost")):
            instance.save()

        return instance
# ---------- Formset de TAREAS (categoría/subcategoría) ----------
TaskFormSet = inlineformset_factory(
    WorkOrder, WorkOrderTask,
    fields=['category','subcategory','description','hours_spent','is_external','labor_rate'],
    widgets={
        'category': forms.Select(attrs={
            'class': 'select2-ajax', 'data-url': reverse_lazy('category-list')
        }),
        'subcategory': forms.Select(attrs={
            'class': 'select2-ajax', 'data-url': reverse_lazy('subcategory-list')
        }),
    },
    extra=1, can_delete=True
)

# ---------- Quick-Create Forms (para crear sin salir) ----------
class QuickCreateVehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate'] if Vehicle and _field_exists(Vehicle, 'plate') else []

class QuickCreateDriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = []
        if Driver:
            opts = []
            for fname in ('full_name','name'):
                if _field_exists(Driver, fname):
                    opts.append(fname)
                    break
            if _field_exists(Driver, 'is_active'):
                opts.append('is_active')
            fields = opts

class QuickCreateCategoryForm(forms.ModelForm):
    class Meta:
        model = TaskCategory
        fields = ['name'] if TaskCategory and _field_exists(TaskCategory, 'name') else []

class QuickCreateSubcategoryForm(forms.ModelForm):
    class Meta:
        model = TaskSubcategory
        fields = []
        if TaskSubcategory:
            opts = []
            if _field_exists(TaskSubcategory, 'name'):
                opts.append('name')
            if _field_exists(TaskSubcategory, 'category') and TaskCategory:
                opts.append('category')
            fields = opts
