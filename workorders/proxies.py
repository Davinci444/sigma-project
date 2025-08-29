# workorders/proxies.py
from .models import WorkOrder

class PreventiveOrder(WorkOrder):
    class Meta:
        proxy = True
        verbose_name = "Orden de Trabajo Preventiva"
        verbose_name_plural = "Órdenes de Trabajo Preventivas"

class CorrectiveOrder(WorkOrder):
    class Meta:
        proxy = True
        verbose_name = "Orden de Trabajo Correctiva"
        verbose_name_plural = "Órdenes de Trabajo Correctivas"
