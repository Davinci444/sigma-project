# core/management/commands/run_daily_jobs.py
"""Management command to process daily fuel fills and related tasks."""

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
    """Handle daily processing of fuel files and maintenance updates."""

    help = "Procesa tanqueos, novedades y recalcula los planes de mantenimiento."

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "--file_path",
            type=str,
            required=False,
            help="Ruta opcional al archivo XLSX a procesar.",
        )

    def handle(self, *args, **kwargs):
        """Execute the command."""
        file_path = kwargs.get("file_path")

        if not file_path:
            file_path_input = input("Por favor, arrastra el archivo 'GESTION DE COMBUSTIBLE.XLSX' a esta ventana y presiona Enter: ").strip()
            file_path = file_path_input.strip('"')

        if not file_path or not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR("No se proporcionó una ruta de archivo válida. Proceso cancelado."))
            return

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Iniciando proceso desde '{os.path.basename(file_path)}'"))

        self.process_tanqueos(file_path)
        self.process_novedades(file_path)
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Proceso de ingesta de archivo completado."))

    def process_tanqueos(self, file_path):
        """Import fuel fill records from the provided Excel file."""
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
        df['PLACA'] = df['PLACA'].astype(str).str.upper().str.strip().str.replace('-', '')
        df.dropna(subset=['FECHA', 'KILOMETRAJE'], inplace=True)
        df = df.sort_values(by='FECHA')

        processed_count = 0
        new_readings = 0
        not_found_plates = set()

        with transaction.atomic():
            for index, row in df.iterrows():
                placa = row['PLACA']
                kilometraje = int(row['KILOMETRAJE'])
                if kilometraje <= 0: continue
                try:
                    vehicle = Vehicle.objects.get(plate=placa)
                except Vehicle.DoesNotExist:
                    not_found_plates.add(placa)
                    continue
                
                if kilometraje < vehicle.current_odometer_km:
                    Alert.objects.get_or_create(...)
                    OdometerReading.objects.create(...)
                    continue

                if not FuelFill.objects.filter(vehicle=vehicle, fill_date=row['FECHA'], odometer_km=kilometraje).exists():
                    FuelFill.objects.create(...)
                    OdometerReading.objects.create(...)
                    vehicle.current_odometer_km = kilometraje
                    vehicle.save()
                    new_readings += 1
                
                processed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Tanqueos procesados: {processed_count}. Nuevas lecturas válidas: {new_readings}."))
        if not_found_plates:
            self.stdout.write(self.style.WARNING(f"{len(not_found_plates)} placas del archivo no fueron encontradas en la base de datos."))
            sample = list(not_found_plates)[:5]
            self.stdout.write(self.style.WARNING(f"Ejemplos de placas no encontradas: {', '.join(sample)}. Verifique que coincidan exactamente."))

    def process_novedades(self, file_path):
        """Process odometer issues from the spreadsheet."""
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
        df['VEHICULO'] = df['VEHICULO'].astype(str).str.upper().str.strip().str.replace('-', '')
        df['OBSERVACIONES'] = df['OBSERVACIONES'].astype(str).str.lower()

        frase_clave = "kilometraje no le sirve/detenido"
        df_problemas = df[df['OBSERVACIONES'].str.contains(frase_clave, na=False)]

        novedades_procesadas = 0
        not_found_plates_novedades = set()
        with transaction.atomic():
            for index, row in df_problemas.iterrows():
                placa = row['VEHICULO']
                observacion = row['OBSERVACIONES']
                try:
                    vehicle = Vehicle.objects.get(plate=placa)
                    if vehicle.odometer_status == Vehicle.OdometerStatus.INVALID:
                        continue
                    vehicle.odometer_status = Vehicle.OdometerStatus.INVALID
                    vehicle.save()
                    Alert.objects.get_or_create(...)
                    novedades_procesadas += 1
                except Vehicle.DoesNotExist:
                    not_found_plates_novedades.add(placa)
                    continue

        self.stdout.write(self.style.SUCCESS(f"Novedades de odómetro procesadas: {novedades_procesadas} vehículos actualizados a 'Inválido'."))
        if not_found_plates_novedades:
            self.stdout.write(self.style.WARNING(f"{len(not_found_plates_novedades)} placas de la hoja de novedades no fueron encontradas en la base de datos."))

