# core/management/commands/run_daily_jobs.py

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import os
from datetime import timedelta

from fleet.models import Vehicle
from core.models import FuelFill, OdometerReading, Alert
from workorders.models import MaintenancePlan


class Command(BaseCommand):
    help = "Procesa tanqueos, novedades y recalcula los planes de mantenimiento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file_path", type=str, help="La ruta completa al archivo XLSX a procesar."
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs.get("file_path")
        if not file_path:
            self.stdout.write(
                self.style.ERROR(
                    "Error: Se debe proporcionar la ruta del archivo con --file_path."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"[{timezone.now()}] Iniciando proceso desde '{os.path.basename(file_path)}'"
            )
        )

        self.process_tanqueos(file_path)
        self.process_novedades(file_path)
        self.recalculate_maintenance_plans()  # <-- NUEVA FUNCIÓN

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Proceso completado."))

    def process_tanqueos(self, file_path):
        # ... (esta función se queda exactamente igual que antes)
        self.stdout.write(self.style.WARNING("\n--- Procesando Hoja de TANQUEOS ---"))
        try:
            df = pd.read_excel(file_path, sheet_name="TANQUEOS")
            self.stdout.write(
                f"Archivo leído. Se encontraron {len(df)} registros de tanqueo."
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"No se pudo leer la hoja 'TANQUEOS': {e}")
            )
            return

        df.columns = [str(col).strip().upper() for col in df.columns]
        required_columns = ["FECHA", "PLACA", "KILOMETRAJE"]
        if not all(col in df.columns for col in required_columns):
            self.stdout.write(
                self.style.ERROR(
                    f"La hoja 'TANQUEOS' debe contener las columnas: {', '.join(required_columns)}"
                )
            )
            return

        df.dropna(subset=["PLACA", "KILOMETRAJE"], inplace=True)
        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
        df["KILOMETRAJE"] = pd.to_numeric(df["KILOMETRAJE"], errors="coerce")
        df["PLACA"] = df["PLACA"].astype(str).str.upper().str.strip()
        df.dropna(subset=["FECHA", "KILOMETRAJE"], inplace=True)
        df = df.sort_values(by="FECHA")

        processed_count = 0
        new_readings = 0
        with transaction.atomic():
            for index, row in df.iterrows():
                placa = row["PLACA"]
                kilometraje = int(row["KILOMETRAJE"])
                if kilometraje <= 0:
                    continue
                try:
                    vehicle = Vehicle.objects.get(plate=placa)
                except Vehicle.DoesNotExist:
                    continue

                if kilometraje < vehicle.current_odometer_km:
                    Alert.objects.get_or_create(
                        alert_type=Alert.AlertType.ODOMETER_INCONSISTENT,
                        related_vehicle=vehicle,
                        defaults={
                            "severity": Alert.Severity.WARNING,
                            "message": f"Lectura de KM para {placa} ({kilometraje} km) es menor a la anterior ({vehicle.current_odometer_km} km).",
                        },
                    )
                    OdometerReading.objects.create(
                        vehicle=vehicle,
                        reading_km=kilometraje,
                        reading_date=row["FECHA"],
                        source=OdometerReading.Source.FUEL_FILL,
                        is_anomaly=True,
                        notes=f"Lectura anómala. Anterior: {vehicle.current_odometer_km} km.",
                    )
                    continue

                if not FuelFill.objects.filter(
                    vehicle=vehicle, fill_date=row["FECHA"], odometer_km=kilometraje
                ).exists():
                    FuelFill.create(...)
                    OdometerReading.create(...)
                    vehicle.current_odometer_km = kilometraje
                    vehicle.save()
                    new_readings += 1

                processed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Tanqueos procesados: {processed_count}. Nuevas lecturas válidas: {new_readings}."
            )
        )

    def process_novedades(self, file_path):
        # ... (esta función se queda exactamente igual que antes)
        self.stdout.write(self.style.WARNING("\n--- Procesando Hoja de NOVEDADES ---"))
        try:
            df = pd.read_excel(file_path, sheet_name="NOVEDADES")
            self.stdout.write(
                f"Archivo leído. Se encontraron {len(df)} registros de novedades."
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"No se pudo leer la hoja 'NOVEDADES': {e}")
            )
            return

        df.columns = [str(col).strip().upper() for col in df.columns]
        required_columns = ["VEHICULO", "OBSERVACIONES"]
        if not all(col in df.columns for col in required_columns):
            self.stdout.write(
                self.style.ERROR(
                    f"La hoja 'NOVEDADES' debe contener las columnas: {', '.join(required_columns)}"
                )
            )
            return

        df.dropna(subset=["VEHICULO", "OBSERVACIONES"], inplace=True)
        df["VEHICULO"] = df["VEHICULO"].astype(str).str.upper().str.strip()
        df["OBSERVACIONES"] = df["OBSERVACIONES"].astype(str).str.lower()

        frase_clave = "kilometraje no le sirve/detenido"
        df_problemas = df[df["OBSERVACIONES"].str.contains(frase_clave, na=False)]

        novedades_procesadas = 0
        with transaction.atomic():
            for index, row in df_problemas.iterrows():
                placa = row["VEHICULO"]
                observacion = row["OBSERVACIONES"]

                try:
                    vehicle = Vehicle.objects.get(plate=placa)
                    if vehicle.odometer_status == Vehicle.OdometerStatus.INVALID:
                        continue

                    vehicle.odometer_status = Vehicle.OdometerStatus.INVALID
                    vehicle.save()

                    Alert.objects.get_or_create(
                        alert_type=Alert.AlertType.ODOMETER_UNAVAILABLE,
                        related_vehicle=vehicle,
                        defaults={
                            "severity": Alert.Severity.CRITICAL,
                            "message": f"Odómetro de {placa} reportado como dañado. Novedad: '{observacion}'. Mantenimiento por KM pausado.",
                        },
                    )
                    novedades_procesadas += 1
                except Vehicle.DoesNotExist:
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Novedades de odómetro procesadas: {novedades_procesadas} vehículos actualizados a 'Inválido'."
            )
        )

    def recalculate_maintenance_plans(self):
        self.stdout.write(
            self.style.WARNING(
                "\n--- Recalculando Planes de Mantenimiento y Generando Alertas ---"
            )
        )

        active_plans = MaintenancePlan.objects.filter(is_active=True).select_related(
            "vehicle"
        )
        alerts_created = 0

        for plan in active_plans:
            vehicle = plan.vehicle

            # Estrategia 1: Kilometraje (si el odómetro es válido)
            if vehicle.odometer_status == Vehicle.OdometerStatus.VALID:
                next_due_km = plan.last_service_km + plan.threshold_km
                km_remaining = next_due_km - vehicle.current_odometer_km

                # Alerta de Vencimiento por KM
                if km_remaining <= plan.grace_km:
                    # Usamos get_or_create para no duplicar la misma alerta
                    _, created = Alert.objects.get_or_create(
                        alert_type=Alert.AlertType.PREVENTIVE_DUE,
                        related_vehicle=vehicle,
                        seen=False,  # Solo creamos si no hay una alerta abierta para esto
                        defaults={
                            "severity": (
                                Alert.Severity.CRITICAL
                                if km_remaining <= 0
                                else Alert.Severity.WARNING
                            ),
                            "message": f"Mantenimiento preventivo para {vehicle.plate} requerido. "
                            f"Vencido por KM. Próximo servicio a los {next_due_km} km (faltan {km_remaining} km).",
                        },
                    )
                    if created:
                        alerts_created += 1

            # Estrategia 2: Tiempo (como respaldo si el odómetro es inválido o como plan principal)
            else:  # vehicle.odometer_status == Vehicle.OdometerStatus.INVALID
                if plan.last_service_date:
                    next_due_date = plan.last_service_date + timedelta(
                        days=plan.threshold_days
                    )
                    days_remaining = (next_due_date - timezone.now().date()).days

                    # Alerta de Vencimiento por Tiempo
                    if days_remaining <= 30:  # Alertar con 30 días de antelación
                        _, created = Alert.objects.get_or_create(
                            alert_type=Alert.AlertType.PREVENTIVE_DUE,
                            related_vehicle=vehicle,
                            seen=False,
                            defaults={
                                "severity": (
                                    Alert.Severity.CRITICAL
                                    if days_remaining <= 0
                                    else Alert.Severity.WARNING
                                ),
                                "message": f"Mantenimiento preventivo para {vehicle.plate} requerido. "
                                f"Vencido por TIEMPO (Odómetro inválido). Próximo servicio el {next_due_date} (faltan {days_remaining} días).",
                            },
                        )
                        if created:
                            alerts_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Recálculo completado. {alerts_created} nuevas alertas de mantenimiento generadas."
            )
        )
