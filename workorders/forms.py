# workorders/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import FieldDoesNotExist

from .models import (
    WorkOrder, WorkOrderTask, WorkOrderAttachment, WorkOrderDriver, WorkOrderNote
)
from users.models import Driver

# ---------- util ----------
def _field_exists(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False

# ---------- Form principal unificado ----------
class WorkOrderUnifiedForm(forms.ModelForm):
    # Conductor y % de responsabilidad
    driver = forms.ModelChoiceField(
        label="Conductor responsable",
        queryset=Driver.objects.filter(is_active=True),
        required=False
    )
    driver_responsibility = forms.DecimalField(
        label="Responsabilidad del conductor (%)",
        required=False, min_value=0, max_value=100
    )

    # Campos SOLO para Correctivo
    pre_diagnosis = forms.CharField(
        label="Pre-diagnóstico (solo correctivo)",
        required=False, widget=forms.Textarea(attrs={'rows':3})
    )
    failure_origin = forms.ChoiceField(
        label="Origen de la falla (solo correctivo)",
        choices=WorkOrder.FailureOrigin.choices, required=False
    )
    severity = forms.ChoiceField(
        label="Severidad (solo correctivo)",
        choices=WorkOrder.Severity.choices, required=False
    )

    # Nota rápida y “causas probables” como novedad
    first_comment = forms.CharField(
        label="Comentario inicial (opcional)",
        required=False, widget=forms.Textarea(attrs={'rows':2})
    )
    probable_causes = forms.CharField(
        label="Causas probables (opcional, solo correctivo)",
        required=False, widget=forms.Textarea(attrs={'rows':2})
    )

    # Campos de fecha/hora "reales" si existen en tu modelo
    dynamic_datetime_fields = ("actual_start", "actual_end", "received_at", "delivered_at", "started_at", "finished_at")

    class Meta:
        model = WorkOrder
        fields = [
            'order_type', 'vehicle', 'description',
            'status', 'priority',
            'scheduled_start', 'scheduled_end',
            'odometer_at_service',
        ]
        widgets = {
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregamos dinámicamente campos datetime si existen
        for fname in self.dynamic_datetime_fields:
            if _field_exists(WorkOrder, fname):
                self.fields[fname] = forms.DateTimeField(
                    required=False,
                    widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                    label=fname.replace("_", " ").capitalize()
                )

    def save(self, user=None, commit=True):
        instance = super().save(commit=commit)

        # Conductor / responsabilidad
        driver = self.cleaned_data.get('driver')
        resp = self.cleaned_data.get('driver_responsibility')
        if driver:
            WorkOrderDriver.objects.update_or_create(
                work_order=instance, driver=driver,
                defaults={'responsibility_percent': resp}
            )

        # Comentario inicial
        comment = self.cleaned_data.get('first_comment')
        if comment:
            WorkOrderNote.objects.create(
                work_order=instance, text=comment, author=user
            )

        # Causas probables -> novedad
        causas = self.cleaned_data.get('probable_causes')
        if causas and self.cleaned_data.get('order_type') == WorkOrder.OrderType.CORRECTIVE:
            WorkOrderNote.objects.create(
                work_order=instance, text=f"Causas probables: {causas}", author=user
            )

        # Correctivo: guarda 3 campos; Preventivo: limpia pre_diagnóstico
        if self.cleaned_data.get('order_type') == WorkOrder.OrderType.CORRECTIVE:
            instance.pre_diagnosis = self.cleaned_data.get('pre_diagnosis')
            instance.failure_origin = self.cleaned_data.get('failure_origin') or instance.failure_origin
            instance.severity = self.cleaned_data.get('severity') or instance.severity
            instance.save(update_fields=['pre_diagnosis','failure_origin','severity'])
        else:
            if hasattr(instance, 'pre_diagnosis') and instance.pre_diagnosis:
                instance.pre_diagnosis = ""
                instance.save(update_fields=['pre_diagnosis'])

        # Guardar campos datetime “reales”, si existen
        for fname in self.dynamic_datetime_fields:
            if fname in self.fields:
                setattr(instance, fname, self.cleaned_data.get(fname))
        if any(fname in self.fields for fname in self.dynamic_datetime_fields):
            instance.save()

        return instance

# ---------- Formsets dentro de la misma pantalla ----------
TaskFormSet = inlineformset_factory(
    WorkOrder, WorkOrderTask,
    fields=['category','subcategory','description','hours_spent','is_external','labor_rate'],
    extra=1, can_delete=True
)

EvidenceURLFormSet = inlineformset_factory(
    WorkOrder, WorkOrderAttachment,
    fields=['url','description'], extra=1, can_delete=True,
    widgets={'url': forms.URLInput(attrs={'placeholder': 'https://(Drive/Dropbox/etc.)'})}
)

class WorkOrderNoteForm(forms.ModelForm):
    class Meta:
        model = WorkOrderNote
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'rows':2, 'placeholder': 'Escribe una novedad...'})}
        labels = {'text': 'Nueva novedad'}
