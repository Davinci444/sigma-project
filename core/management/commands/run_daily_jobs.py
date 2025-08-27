# core/management/commands/run_daily_jobs.py

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import os

from fleet.models import Vehicle
from core.models import FuelFill, OdometerReading, Alert

class Command(BaseCommand):
    help = "Procesa tanqueos y novedades desde el archivo de gestión de combustible."

    def add_arguments(self, parser):
        parser.add_argument('--file_path', type=str, help='La ruta completa al archivo XLSX a procesar.')

    def handle(self, *args, **kwargs):
        file_path = kwargs.get('file_path')
        if not file_path:
            self.stdout.write(self.style.ERROR("Error: Se debe proporcionar la ruta del archivo con --file_path."))
            return

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Iniciando proceso desde '{os.path.basename(file_path)}'"))

        # --- Parte 1: Procesar Tanqueos ---
        self.process_tanqueos(file_path)

        # --- Parte 2: Procesar Novedades ---
        self.process_novedades(file_path)

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Proceso completado."))

    def process_tanqueos(self, file_path):
        self.stdout.write(self.style.WARNING("\n--- Procesando Hoja de TANQUEOS ---"))
        try:
            df = pd.read_excel(file_path, sheet_name='TANQUEOS')
            self.stdout.write(f"Archivo leído. Se encontraron {len(df)} registros de tanqueo.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"No se pudo leer la hoja 'TANQUEOS': {e}"))
            return

        df.columns = [str(col).strip().upper() for col in df.columns]
        required_columns = ['FECHA', 'PLACA', 'KILOMETRAJE']
        if not all(col in df.columns for col in required_columns):
            self.stdout.write(self.style.ERROR(f"La hoja 'TANQUEOS' debe contener las columnas: {', '.join(required_columns)}"))
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
                kilometraje = int(row['KILOMETRAJE'])
                if kilometraje <= 0: continue
                try:
                    vehicle = Vehicle.objects.get(plate=placa)
                except Vehicle.DoesNotExist:
                    continue
                
                # (La lógica de validación de monotonía y guardado de datos se queda igual)
                if kilometraje < vehicle.current_odometer_km:
                    # ... (código de anomalía)
                    continue

                if not FuelFill.objects.filter(vehicle=vehicle, fill_date=row['FECHA'], odometer_km=kilometraje).exists():
                    # ... (código para crear FuelFill y OdometerReading)
                    vehicle.current_odometer_km = kilometraje
                    vehicle.save()
                    new_readings += 1
                
                processed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Tanqueos procesados: {processed_count}. Nuevas lecturas válidas: {new_readings}."))

    def process_novedades(self, file_path):
        self.stdout.write(self.style.WARNING("\n--- Procesando Hoja de NOVEDADES ---"))
        try:
            df = pd.read_excel(file_path, sheet_name='NOVEDADES')
            self.stdout.write(f"Archivo leído. Se encontraron {len(df)} registros de novedades.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"No se pudo leer la hoja 'NOVEDADES': {e}"))
            return

        df.columns = [str(col).strip().upper() for col in df.columns]
        required_columns = ['VEHICULO', 'OBSERVACIONES']
        if not all(col in df.columns for col in required_columns):
            self.stdout.write(self.style.ERROR(f"La hoja 'NOVEDADES' debe contener las columnas: {', '.join(required_columns)}"))
            return
        
        df.dropna(subset=['VEHICULO', 'OBSERVACIONES'], inplace=True)
        df['VEHICULO'] = df['VEHICULO'].astype(str).str.upper().str.strip()
        df['OBSERVACIONES'] = df['OBSERVACIONES'].astype(str).str.lower()

        # Frase clave que buscaremos
        frase_clave = "kilometraje no le sirve/detenido"
        
        # Filtramos solo las filas que contienen la frase clave
        df_problemas = df[df['OBSERVACIONES'].str.contains(frase_clave, na=False)]

        novedades_procesadas = 0
        with transaction.atomic():
            for index, row in df_problemas.iterrows():
                placa = row['VEHICULO']
                observacion = row['OBSERVACIONES']

                try:
                    vehicle = Vehicle.objects.get(plate=placa)
                    
                    # Si el odómetro ya está marcado como inválido, no hacemos nada.
                    if vehicle.odometer_status == Vehicle.OdometerStatus.INVALID:
                        continue

                    # Si no, lo actualizamos y creamos la alerta.
                    vehicle.odometer_status = Vehicle.OdometerStatus.INVALID
                    vehicle.save()

                    Alert.objects.create(
                        alert_type=Alert.AlertType.ODOMETER_UNAVAILABLE,
                        severity=Alert.Severity.CRITICAL,
                        message=f"Odómetro de {placa} reportado como dañado. Novedad: '{observacion}'. Mantenimiento por KM pausado.",
                        related_vehicle=vehicle
                    )
                    novedades_procesadas += 1

                except Vehicle.DoesNotExist:
                    continue # Ignoramos novedades de vehículos que no existen

        self.stdout.write(self.style.SUCCESS(f"Novedades de odómetro procesadas: {novedades_procesadas} vehículos actualizados a estado 'Inválido'."))

