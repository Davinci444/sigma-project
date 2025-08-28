# core/management/commands/seed_manuals.py
from django.core.management.base import BaseCommand
from django.db import transaction
from workorders.models import MaintenanceManual, ManualTask
from fleet.models import Vehicle


class Command(BaseCommand):
    help = "Crea los manuales de mantenimiento estándar para Diésel y Gasolina."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.SUCCESS("Iniciando la creación de manuales de mantenimiento...")
        )

        # --- Plan de Mantenimiento DIÉSEL ---
        diesel_manual, created = MaintenanceManual.objects.get_or_create(
            name="Plan Preventivo Estándar - Diésel",
            defaults={"fuel_type": Vehicle.FuelType.DIESEL},
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS('Manual "Plan Preventivo Estándar - Diésel" creado.')
            )
            tasks_diesel = {
                10000: [
                    "Cambiar aceite y filtro de motor",
                    "Inspección de fugas",
                    "Purgar separador de agua",
                    "Inspeccionar filtro de aire",
                    "Verificar nivel de refrigerante",
                    "Lubricar crucetas y cardán",
                    "Inspeccionar dirección y suspensión",
                    "Revisar frenos y drenar tanques de aire",
                    "Inspeccionar y rotar neumáticos",
                    "Prueba de sistema eléctrico y escaneo OBD",
                ],
                20000: [
                    "Reemplazar filtro(s) de combustible",
                    "Reemplazar filtro de aire",
                    "Servicio de frenos detallado",
                ],
                40000: [
                    "Cambiar aceite de transmisión y diferenciales",
                    "Cambiar líquido de frenos y dirección",
                    "Revisar correas auxiliares y tensores",
                    "Revisar cartucho secador de aire",
                ],
                60000: [
                    "Ajuste de válvulas (si aplica)",
                    "Revisar filtro de ventilación del cárter (CCV)",
                ],
                80000: ["Evaluación de turbo y limpieza de intercooler"],
                100000: [
                    "Revisión/Cambio de correa de distribución y bomba de agua",
                    "Limpieza/Inspección de DPF",
                ],
            }
            self.create_tasks_for_manual(diesel_manual, tasks_diesel)

        # --- Plan de Mantenimiento GASOLINA ---
        gasolina_manual, created = MaintenanceManual.objects.get_or_create(
            name="Plan Preventivo Estándar - Gasolina",
            defaults={"fuel_type": Vehicle.FuelType.GASOLINE},
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    'Manual "Plan Preventivo Estándar - Gasolina" creado.'
                )
            )
            tasks_gasolina = {
                10000: [
                    "Cambiar aceite y filtro de motor",
                    "Inspección de fugas",
                    "Inspeccionar filtro de aire",
                    "Revisar sistema de refrigeración",
                    "Revisar frenos, dirección y suspensión",
                    "Inspeccionar y rotar neumáticos",
                    "Prueba de sistema eléctrico y escaneo OBD",
                ],
                20000: [
                    "Reemplazar filtro de aire",
                    "Reemplazar filtro de cabina (A/C)",
                    "Alineación y balanceo preventivo",
                ],
                40000: [
                    "Reemplazar bujías (convencionales)",
                    "Reemplazar filtro de combustible (si es externo)",
                    "Cambiar líquido de frenos",
                    "Cambiar aceite de transmisión (ATF/CVT)",
                ],
                60000: ["Revisar correa de accesorios y tensores"],
                80000: ["Cambiar refrigerante (si no es de larga duración)"],
                100000: [
                    "Cambio de correa de distribución y bomba de agua (si aplica)",
                    "Revisión de sensor de oxígeno y catalizador",
                ],
            }
            self.create_tasks_for_manual(gasolina_manual, tasks_gasolina)

        self.stdout.write(
            self.style.SUCCESS("Proceso de siembra de manuales completado.")
        )

    def create_tasks_for_manual(self, manual, tasks_dict):
        # Función para crear las tareas de forma acumulativa
        all_tasks_for_milestone = set()
        for milestone in sorted(tasks_dict.keys()):
            # Añadimos las tareas base de 10k a todos los hitos
            if milestone > 10000:
                for task_desc in tasks_dict.get(10000, []):
                    all_tasks_for_milestone.add(task_desc)

            # Añadimos las tareas específicas de este hito
            for task_desc in tasks_dict[milestone]:
                all_tasks_for_milestone.add(task_desc)

            # Guardamos todas las tareas para este hito
            for desc in sorted(list(all_tasks_for_milestone)):
                ManualTask.objects.create(
                    manual=manual, km_interval=milestone, description=desc
                )

            self.stdout.write(
                f"  - Creadas {len(all_tasks_for_milestone)} tareas para el hito de {milestone} km del manual {manual.name}."
            )
