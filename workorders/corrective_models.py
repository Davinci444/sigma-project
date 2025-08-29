# workorders/corrective_models.py
"""Modelos de soporte para correctivos: pre-diagnóstico y conductores responsables."""

from django.db import models
from .models import WorkOrder
from users.models import Driver


class WorkOrderCorrective(models.Model):
    """
    Datos específicos para OTs CORRECTIVAS.
    Un registro por OT (OneToOne).
    """
    work_order = models.OneToOneField(
        WorkOrder, on_delete=models.CASCADE, related_name="corrective"
    )
    pre_diagnosis = models.TextField("Pre diagnóstico", blank=True)

    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        verbose_name = "Datos de Correctivo"
        verbose_name_plural = "Datos de Correctivos"

    def __str__(self) -> str:
        return f"Correctivo OT #{self.work_order_id}"


class WorkOrderDriverAssignment(models.Model):
    """
    Asignación de conductores responsables para OTs CORRECTIVAS.
    Se permite múltiples responsables por OT.
    """
    class Role(models.TextChoices):
        RESPONSABLE = "RESP", "Responsable"
        CO_RESPONSABLE = "CORESP", "Co-responsable"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="driver_assignments"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT, related_name="assignments"
    )
    role = models.CharField("Rol", max_length=10, choices=Role.choices, default=Role.RESPONSABLE)
    notes = models.CharField("Notas", max_length=200, blank=True)

    assigned_at = models.DateTimeField("Asignado", auto_now_add=True)

    class Meta:
        verbose_name = "Conductor asignado"
        verbose_name_plural = "Conductores asignados"
        unique_together = ("work_order", "driver")
        ordering = ["-assigned_at"]

    def __str__(self) -> str:
        return f"OT #{self.work_order_id} - {self.driver} [{self.get_role_display()}]"
