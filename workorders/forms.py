# workorders/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import WorkOrder, WorkOrderTask, WorkOrderAttachment, WorkOrderDriver, WorkOrderNote
from users.models import Driver

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

    # Nota rápida y causas probables (se guardan como Novedades)
    first_comment = forms.CharField(
        label="Comentario inicial (opcional)",
        required=False, widget=forms.Textarea(attrs={'rows':2})
    )
    probable_causes = forms.CharField(
        label="Causas probables (opcional, solo correctivo)",
        required=False, widget=forms.Textarea(attrs={'rows':2})
    )

    class Meta:
        model = WorkOrder
        fields = [
            'order_type', 'vehicle', 'description',
            'status', 'priority',
            'scheduled_start', 'scheduled_end',
            'odometer_at_service',
            # los 3 de correctivo arriba se muestran/ocultan por JS
        ]
        widgets = {
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows':3}),
        }

    def save(self, user=None, commit=True):
        instance = super().save(commit=commit)

        # Conductor
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

        # Causas probables -> nota
        causas = self.cleaned_data.get('probable_causes')
        if causas:
            WorkOrderNote.objects.create(
                work_order=instance, text=f"Causas probables: {causas}", author=user
            )

        # Si es Correctivo, guardamos los 3 campos; si no, los limpiamos
        if self.cleaned_data.get('order_type') == WorkOrder.OrderType.CORRECTIVE:
            instance.pre_diagnosis = self.cleaned_data.get('pre_diagnosis')
            instance.failure_origin = self.cleaned_data.get('failure_origin') or instance.failure_origin
            instance.severity = self.cleaned_data.get('severity') or instance.severity
            instance.save(update_fields=['pre_diagnosis','failure_origin','severity'])
        else:
            # para evitar "ruido" en preventivo
            cleared = False
            if hasattr(instance, 'pre_diagnosis') and instance.pre_diagnosis:
                instance.pre_diagnosis = ""
                cleared = True
            if cleared:
                instance.save(update_fields=['pre_diagnosis'])

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

# ---------- Nota rápida en "Novedades" ----------
class WorkOrderNoteForm(forms.ModelForm):
    class Meta:
        model = WorkOrderNote
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'rows':2, 'placeholder': 'Escribe una novedad...'})}
        labels = {'text': 'Nueva novedad'}
