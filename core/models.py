# core/models.py

from django.db import models
from django.conf import settings

class Alert(models.Model):
    class AlertType(models.TextChoices):
        DOC_EXPIRATION = 'DOC_EXPIRATION', 'Vencimiento de Documento'
        LOW_STOCK = 'LOW_STOCK', 'Stock Bajo'
        PREVENTIVE_DUE = 'PREVENTIVE_DUE', 'Preventivo Pendiente'
        URGENT_OT = 'URGENT_OT', 'OT Urgente Creada'

    class Severity(models.TextChoices):
        INFO = 'INFO', 'Informativa'
        WARNING = 'WARNING', 'Advertencia'
        CRITICAL = 'CRITICAL', 'Crítica'

    alert_type = models.CharField("Tipo de Alerta", max_length=30, choices=AlertType.choices)
    message = models.CharField("Mensaje", max_length=255)
    severity = models.CharField("Severidad", max_length=20, choices=Severity.choices, default=Severity.INFO)
    
    # Enlace a la entidad relacionada
    related_vehicle = models.ForeignKey('fleet.Vehicle', on_delete=models.CASCADE, null=True, blank=True)
    related_part = models.ForeignKey('inventory.Part', on_delete=models.CASCADE, null=True, blank=True)
    related_work_order = models.ForeignKey('workorders.WorkOrder', on_delete=models.CASCADE, null=True, blank=True)
    
    seen = models.BooleanField("Vista", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.message}"

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-created_at']