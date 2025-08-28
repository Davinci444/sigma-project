# core/management/commands/run_periodic_checks.py
"""Management command for periodic system checks and maintenance seeding."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import models, transaction
from fleet.models import Vehicle
from core.models import Alert
from workorders.models import MaintenancePlan, MaintenanceManual, ManualTask


class Command(BaseCommand):
    """Execute periodic checks such as document expiration and manual seeding."""

    help = "Ejecuta revisiones y siembra los manuales de mantenimiento si es necesario."

    def handle(self, *args, **kwargs):
        """Run scheduled tasks."""

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Iniciando Tareas Programadas..."))
        self.seed_maintenance_manuals()
        self.check_document_expirations()
        self.recalculate_maintenance_plans()
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Tareas Programadas completadas."))

    def seed_maintenance_manuals(self):
        """Ensure default maintenance manuals exist."""

        self.stdout.write(self.style.WARNING("\n--- Verificando Manuales de Mantenimiento ---"))
        
        # --- Plan de Mantenimiento DIÉSEL ---
        diesel_manual, created = MaintenanceManual.objects.get_or_create(
            name='Plan Preventivo Estándar - Diésel',
            defaults={'fuel_type': Vehicle.FuelType.DIESEL}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Manual "Plan Preventivo Estándar - Diésel" creado.'))
            tasks_diesel = {
                10000: ['Cambiar aceite y filtro de motor', 'Inspección de fugas', 'Purgar separador de agua', 'Inspeccionar filtro de aire', 'Verificar nivel de refrigerante', 'Lubricar crucetas y cardán', 'Inspeccionar dirección y suspensión', 'Revisar frenos y drenar tanques de aire', 'Inspeccionar y rotar neumáticos', 'Prueba de sistema eléctrico y escaneo OBD'],
                20000: ['Reemplazar filtro(s) de combustible', 'Reemplazar filtro de aire', 'Servicio de frenos detallado'],
                40000: ['Cambiar aceite de transmisión y diferenciales', 'Cambiar líquido de frenos y dirección', 'Revisar correas auxiliares y tensores', 'Revisar cartucho secador de aire'],
                60000: ['Ajuste de válvulas (si aplica)', 'Revisar filtro de ventilación del cárter (CCV)'],
                80000: ['Evaluación de turbo y limpieza de intercooler'],
                100000: ['Revisión/Cambio de correa de distribución y bomba de agua', 'Limpieza/Inspección de DPF']
            }
            self.create_tasks_for_manual(diesel_manual, tasks_diesel)

        # --- Plan de Mantenimiento GASOLINA ---
        gasolina_manual, created = MaintenanceManual.objects.get_or_create(
            name='Plan Preventivo Estándar - Gasolina',
            defaults={'fuel_type': Vehicle.FuelType.GASOLINE}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Manual "Plan Preventivo Estándar - Gasolina" creado.'))
            tasks_gasolina = {
                10000: ['Cambiar aceite y filtro de motor', 'Inspección de fugas', 'Inspeccionar filtro de aire', 'Revisar sistema de refrigeración', 'Revisar frenos, dirección y suspensión', 'Inspeccionar y rotar neumáticos', 'Prueba de sistema eléctrico y escaneo OBD'],
                20000: ['Reemplazar filtro de aire', 'Reemplazar filtro de cabina (A/C)', 'Alineación y balanceo preventivo'],
                40000: ['Reemplazar bujías (convencionales)', 'Reemplazar filtro de combustible (si es externo)', 'Cambiar líquido de frenos', 'Cambiar aceite de transmisión (ATF/CVT)'],
                60000: ['Revisar correa de accesorios y tensores'],
                80000: ['Cambiar refrigerante (si no es de larga duración)'],
                100000: ['Cambio de correa de distribución y bomba de agua (si aplica)', 'Revisión de sensor de oxígeno y catalizador']
            }
            self.create_tasks_for_manual(gasolina_manual, tasks_gasolina)
        
        self.stdout.write(self.style.SUCCESS('Verificación de manuales completada.'))

    def create_tasks_for_manual(self, manual, tasks_dict):
        """Create cumulative tasks for a maintenance manual.

        Args:
            manual (MaintenanceManual): Manual to attach tasks to.
            tasks_dict (dict): Mapping of mileage milestones to task lists.
        """

        all_tasks_for_milestone = set()
        # Creamos las tareas base primero
        base_tasks = tasks_dict.get(10000, [])
        for task_desc in base_tasks:
            ManualTask.objects.create(manual=manual, km_interval=10000, description=task_desc)
        
        # Creamos las tareas acumulativas para los siguientes hitos
        for milestone in sorted(tasks_dict.keys()):
            if milestone == 10000: continue # Ya creamos las base
            
            # Agregamos todas las tareas de hitos anteriores
            previous_milestones = [m for m in tasks_dict.keys() if m < milestone]
            for prev_m in previous_milestones:
                for task_desc in tasks_dict.get(prev_m, []):
                    all_tasks_for_milestone.add(task_desc)

            # Agregamos las tareas específicas de este hito
            for task_desc in tasks_dict[milestone]:
                all_tasks_for_milestone.add(task_desc)
            
            for desc in sorted(list(all_tasks_for_milestone)):
                ManualTask.objects.create(manual=manual, km_interval=milestone, description=desc)
            
            self.stdout.write(f'  - Creadas {len(all_tasks_for_milestone)} tareas para el hito de {milestone} km del manual {manual.name}.')
            all_tasks_for_milestone.clear()

    def check_document_expirations(self):
        """Generate alerts for vehicles with upcoming document expirations."""

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
                    message__contains="SOAT",
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
        """Recalculate maintenance plans and create alerts if needed."""

        self.stdout.write(self.style.WARNING("\n--- Recalculando Planes de Mantenimiento ---"))
        active_plans = MaintenancePlan.objects.filter(is_active=True).select_related('vehicle', 'manual')
        alerts_created = 0

        for plan in active_plans:
            vehicle = plan.vehicle
            if not plan.manual or vehicle.odometer_status != 'VALID':
                continue

            km_since_last_service = vehicle.current_odometer_km - plan.last_service_km
            
            next_task = plan.manual.tasks.filter(km_interval__gt=km_since_last_service).order_by('km_interval').first()
            if not next_task: continue

            next_due_km = plan.last_service_km + next_task.km_interval
            
            if vehicle.current_odometer_km >= (next_due_km - 500):
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
