    # core/management/commands/run_daily_jobs.py

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import os

from fleet.models import Vehicle
from core.models import FuelFill, OdometerReading, Alert

class Command(BaseCommand):
        help = "Procesa un archivo de tanqueos para actualizar el kilometraje."

        # --- NUEVO: Aceptamos un argumento desde la línea de comandos ---
        def add_arguments(self, parser):
            parser.add_argument('--file_path', type=str, help='La ruta completa al archivo XLSX a procesar.')

        def handle(self, *args, **kwargs):
            file_path = kwargs.get('file_path')

            if not file_path:
                self.stdout.write(self.style.ERROR("Error: Se debe proporcionar la ruta del archivo con --file_path."))
                return

            self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Iniciando proceso de ingesta desde '{os.path.basename(file_path)}'"))

            try:
                df = pd.read_excel(file_path, sheet_name='TANQUEOS')
                self.stdout.write(self.style.SUCCESS(f"Archivo leído. Se encontraron {len(df)} registros."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ocurrió un error al leer el archivo Excel: {e}"))
                return

            # (El resto de la lógica de procesamiento es exactamente la misma)
            df.columns = [col.strip().upper() for col in df.columns]

            required_columns = ['FECHA', 'PLACA', 'KILOMETRAJE', 'GALONES']
            if not all(col in df.columns for col in required_columns):
                self.stdout.write(self.style.ERROR(f"El archivo debe contener las columnas: {', '.join(required_columns)}"))
                return

            df.dropna(subset=['PLACA', 'KILOMETRAJE'], inplace=True)
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
            df['KILOMETRAJE'] = pd.to_numeric(df['KILOMETRAJE'], errors='coerce')
            df['PLACA'] = df['PLACA'].astype(str).str.upper().str.strip()
            df.dropna(subset=['FECHA', 'KILOMETRAJE'], inplace=True)
            df = df.sort_values(by='FECHA')

            processed_count = 0
            new_readings = 0
            with transaction.atomic():
                for index, row in df.iterrows():
                    placa = row['PLACA']
                    fecha = row['FECHA']
                    kilometraje = int(row['KILOMETRAJE'])
                    galones = row.get('GALONES', 0)
                    observaciones = row.get('OBSERVACIONES', '')

                    if kilometraje <= 0:
                        continue

                    try:
                        vehicle = Vehicle.objects.get(plate=placa)
                    except Vehicle.DoesNotExist:
                        continue

                    if kilometraje < vehicle.current_odometer_km:
                        Alert.objects.create(
                            alert_type=Alert.AlertType.ODOMETER_INCONSISTENT,
                            severity=Alert.Severity.WARNING,
                            message=f"Lectura de KM para {placa} ({kilometraje} km) es menor a la anterior ({vehicle.current_odometer_km} km). Se marcó como anomalía.",
                            related_vehicle=vehicle
                        )
                        OdometerReading.objects.create(
                            vehicle=vehicle, reading_km=kilometraje, reading_date=fecha,
                            source=OdometerReading.Source.FUEL_FILL, is_anomaly=True,
                            notes=f"Lectura anómala. Anterior: {vehicle.current_odometer_km} km."
                        )
                        continue

                    if not FuelFill.objects.filter(vehicle=vehicle, fill_date=fecha, odometer_km=kilometraje).exists():
                        FuelFill.objects.create(
                            vehicle=vehicle, fill_date=fecha, odometer_km=kilometraje,
                            gallons=galones, notes=observaciones, source_file=os.path.basename(file_path)
                        )
                        OdometerReading.objects.create(
                            vehicle=vehicle, reading_km=kilometraje, reading_date=fecha,
                            source=OdometerReading.Source.FUEL_FILL
                        )
                        vehicle.current_odometer_km = kilometraje
                        vehicle.save()
                        new_readings += 1
                    
                    processed_count += 1

            summary = f"Proceso completado. Registros procesados: {processed_count}. Nuevas lecturas válidas: {new_readings}."
            self.stdout.write(self.style.SUCCESS(summary))

  