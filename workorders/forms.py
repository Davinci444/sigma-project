# workorders/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import WorkOrder, WorkOrderTask, WorkOrderAttachment, WorkOrderDriver
from users.models import Driver

class WorkOrderBaseForm(forms.ModelForm):
    driver = forms.ModelChoiceField(
        label="Conductor responsable",
        queryset=Driver.objects.filter(is_active=True),
        required=False
    )
    driver_responsibility = forms.DecimalField(
        label="Responsabilidad del conductor (%)",
        required=False, min_value=0, max_value=100
    )
    first_comment = forms.CharField(
        label="Comentario inicial (opcional)",
        required=False, widget=forms.Textarea(attrs={'rows':3})
    )

    class Meta:
        model = WorkOrder
        fields = [
            'vehicle', 'order_type', 'status', 'priority',
            'scheduled_start', 'scheduled_end', 'odometer_at_service'
        ]
        widgets = {
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def save(self, user=None, commit=True):
        instance = super().save(commit=commit)
        driver = self.cleaned_data.get('driver')
        resp = self.cleaned_data.get('driver_responsibility')
        if driver:
            WorkOrderDriver.objects.get_or_create(
                work_order=instance, driver=driver,
                defaults={'responsibility_percent': resp}
            )
        comment = self.cleaned_data.get('first_comment')
        if comment:
            from .models import WorkOrderNote
            WorkOrderNote.objects.create(
                work_order=instance, text=comment, author=user
            )
        return instance

class WorkOrderPreventiveForm(WorkOrderBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_type'].initial = WorkOrder.OrderType.PREVENTIVE

class WorkOrderCorrectiveForm(WorkOrderBaseForm):
    pre_diagnosis = forms.CharField(
        label="Pre-diagnóstico",
        required=False, widget=forms.Textarea(attrs={'rows':3})
    )
    failure_origin = forms.ChoiceField(
        label="Origen de la falla",
        choices=WorkOrder.FailureOrigin.choices, required=False
    )
    severity = forms.ChoiceField(
        label="Severidad",
        choices=WorkOrder.Severity.choices, required=False
    )

    class Meta(WorkOrderBaseForm.Meta):
        fields = WorkOrderBaseForm.Meta.fields + ['pre_diagnosis','failure_origin','severity']

EvidenceURLFormSet = inlineformset_factory(
    WorkOrder, WorkOrderAttachment,
    fields=['url','description'], extra=1, can_delete=True,
    widgets={'url': forms.URLInput(attrs={'placeholder': 'Pega aquí el enlace (Drive/Dropbox/etc.)'})}
)

TaskFormSet = inlineformset_factory(
    WorkOrder, WorkOrderTask,
    fields=['category','subcategory','description','hours_spent','is_external','labor_rate'],
    extra=1, can_delete=True
)
