# core/services.py
import pandas as pd
from django.db import transaction
import os

from fleet.models import Vehicle
from core.models import FuelFill, OdometerReading, Alert

def process_fuel_file(file_object, source_filename=''):
    """
    Procesa un archivo de tanqueos (desde un objeto en memoria) y actualiza la BD.
    Retorna un resumen del proceso.
    """
    try:
        df = pd.read_excel(file_object, sheet_name='TANQUEOS')
    except Exception as e:
        raise ValueError(f"No se pudo leer la hoja 'TANQUEOS' del archivo Excel: {e}")

    df.columns = [str(col).strip().upper() for col in df.columns]
    required_columns = ['FECHA', 'PLACA', 'KILOMETRAJE']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"El archivo debe contener las columnas: {', '.join(required_columns)}")

    df.dropna(subset=['PLACA', 'KILOMETRAJE'], inplace=True)
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    df['KILOMETRAJE'] = pd.to_numeric(df['KILOMETRAJE'], errors='coerce')
    df['PLACA'] = df['PLACA'].astype(str).str.upper().str.strip()
    df.dropna(subset=['FECHA', 'KILOMETRAJE'], inplace=True)
    df = df.sort_values(by='FECHA')

    processed_count = 0
    new_readings = 0
    anomalies_found = 0

    with transaction.atomic():
        for index, row in df.iterrows():
            placa = row['PLACA']
            kilometraje = int(row['KILOMETRAJE'])
            if kilometraje <= 0: continue
            
            try:
                vehicle = Vehicle.objects.get(plate=placa)
            except Vehicle.DoesNotExist:
                continue

            if kilometraje < vehicle.current_odometer_km:
                anomalies_found += 1
                OdometerReading.objects.get_or_create(
                    vehicle=vehicle, reading_km=kilometraje, reading_date=row['FECHA'],
                    defaults={'source': OdometerReading.Source.FUEL_FILL, 'is_anomaly': True, 'notes': f"Lectura anómala. Anterior: {vehicle.current_odometer_km} km."}
                )
                continue

            if not FuelFill.objects.filter(vehicle=vehicle, fill_date=row['FECHA'], odometer_km=kilometraje).exists():
                FuelFill.objects.create(
                    vehicle=vehicle, fill_date=row['FECHA'], odometer_km=kilometraje,
                    gallons=row.get('GALONES', 0), notes=row.get('OBSERVACIONES', ''),
                    source_file=source_filename
                )
                OdometerReading.objects.create(
                    vehicle=vehicle, reading_km=kilometraje, reading_date=row['FECHA'],
                    source=OdometerReading.Source.FUEL_FILL
                )
                vehicle.current_odometer_km = kilometraje
                vehicle.save()
                new_readings += 1
            
            processed_count += 1
    
    return f"Registros leídos: {len(df)}. Registros procesados: {processed_count}. Nuevas lecturas válidas: {new_readings}. Anomalías encontradas: {anomalies_found}."
