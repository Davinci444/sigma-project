# core/management/commands/run_periodic_checks.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import models # <-- CORRECCIÓN 1: Importación que faltaba

from fleet.models import Vehicle
from core.models import Alert
from workorders.models import MaintenancePlan

class Command(BaseCommand):
    help = "Ejecuta todas las revisiones periódicas del sistema (documentos, planes, etc.)"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Iniciando revisiones periódicas..."))
        self.check_document_expirations()
        self.recalculate_maintenance_plans()
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Revisiones completadas."))

    def check_document_expirations(self):
        self.stdout.write(self.style.WARNING("\n--- Verificando Vencimiento de Documentos ---"))
        today = timezone.now().date()
        alert_threshold = today + timedelta(days=30)
        alerts_created = 0

        vehicles_to_check = Vehicle.objects.filter(
            models.Q(soat_due_date__lte=alert_threshold) |
            models.Q(rtm_due_date__lte=alert_threshold)
        ).filter(status=Vehicle.VehicleStatus.ACTIVE)

        for vehicle in vehicles_to_check:
            if vehicle.soat_due_date and vehicle.soat_due_date <= alert_threshold:
                days_remaining = (vehicle.soat_due_date - today).days
                _, created = Alert.objects.get_or_create(
                    alert_type=Alert.AlertType.DOC_EXPIRATION,
                    related_vehicle=vehicle,
                    seen=False,
                    message__contains="SOAT", # Evita duplicados si la fecha no cambia
                    defaults={
                        'severity': Alert.Severity.CRITICAL if days_remaining < 0 else Alert.Severity.WARNING,
                        'message': f"SOAT de {vehicle.plate} {'vencido' if days_remaining < 0 else 'próximo a vencer'} ({vehicle.soat_due_date})."
                    }
                )
                if created: alerts_created += 1
            
            if vehicle.rtm_due_date and vehicle.rtm_due_date <= alert_threshold:
                days_remaining = (vehicle.rtm_due_date - today).days
                _, created = Alert.objects.get_or_create(
                    alert_type=Alert.AlertType.DOC_EXPIRATION,
                    related_vehicle=vehicle,
                    seen=False,
                    message__contains="Tecnomecánica",
                    defaults={
                        'severity': Alert.Severity.CRITICAL if days_remaining < 0 else Alert.Severity.WARNING,
                        'message': f"Tecnomecánica de {vehicle.plate} {'vencida' if days_remaining < 0 else 'próxima a vencer'} ({vehicle.rtm_due_date})."
                    }
                )
                if created: alerts_created += 1

        self.stdout.write(self.style.SUCCESS(f"Verificación de documentos completada. {alerts_created} nuevas alertas generadas."))

    def recalculate_maintenance_plans(self):
        self.stdout.write(self.style.WARNING("\n--- Recalculando Planes de Mantenimiento ---"))
        active_plans = MaintenancePlan.objects.filter(is_active=True).select_related('vehicle', 'manual__tasks')
        alerts_created = 0

        for plan in active_plans:
            vehicle = plan.vehicle
            if not plan.manual or vehicle.odometer_status != 'VALID':
                continue # Si no hay manual o el odómetro es inválido, no podemos calcular por KM

            km_since_last_service = vehicle.current_odometer_km - plan.last_service_km
            
            # Buscamos el próximo hito de mantenimiento que le toca
            next_task = plan.manual.tasks.filter(km_interval__gt=km_since_last_service).order_by('km_interval').first()
            if not next_task: continue # Si ya pasó todas las tareas, no hay nada que alertar

            next_due_km = plan.last_service_km + next_task.km_interval
            
            # Si el vehículo está cerca o pasado del próximo mantenimiento
            if vehicle.current_odometer_km >= (next_due_km - 500): # Alerta con 500km de antelación
                _, created = Alert.objects.get_or_create(
                    alert_type=Alert.AlertType.PREVENTIVE_DUE,
                    related_vehicle=vehicle,
                    seen=False,
                    defaults={
                        'severity': Alert.Severity.CRITICAL if vehicle.current_odometer_km >= next_due_km else Alert.Severity.WARNING,
                        'message': f"Mantenimiento preventivo para {vehicle.plate} requerido. "
                                   f"Próximo servicio ({next_task.description}) a los {next_due_km} km."
                    }
                )
                if created: alerts_created += 1
        
        self.stdout.write(self.style.SUCCESS(f"Recálculo de planes completado. {alerts_created} nuevas alertas generadas."))
