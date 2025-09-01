# core/services.py
import logging

import pandas as pd
from django.db import transaction

from fleet.models import Vehicle
from core.models import FuelFill, OdometerReading


logger = logging.getLogger(__name__)

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
    required_columns = ["FECHA", "PLACA", "KILOMETRAJE"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(
            f"El archivo debe contener las columnas: {', '.join(required_columns)}"
        )

    df.dropna(subset=["PLACA", "KILOMETRAJE"], inplace=True)
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    df["KILOMETRAJE"] = pd.to_numeric(df["KILOMETRAJE"], errors="coerce")
    df["PLACA"] = df["PLACA"].astype(str).str.upper().str.strip()
    df.dropna(subset=["FECHA", "KILOMETRAJE"], inplace=True)
    df = df.sort_values(by="FECHA")

    processed_count = 0
    new_readings = 0
    anomalies_found = 0

    plates = df["PLACA"].unique()
    vehicles = Vehicle.objects.filter(plate__in=plates)
    vehicle_map = {v.plate: v for v in vehicles}
    missing = set(plates) - set(vehicle_map.keys())
    if missing:
        logger.warning("Vehículos no encontrados: %s", ", ".join(sorted(missing)))

    fuel_fills = []
    odometer_readings = []
    vehicles_to_update = {}

    with transaction.atomic():
        for idx, row in df.iterrows():
            placa = row["PLACA"]
            kilometraje = int(row["KILOMETRAJE"])
            if kilometraje <= 0:
                continue

            vehicle = vehicle_map.get(placa)
            if not vehicle:
                continue

            try:
                if kilometraje < vehicle.current_odometer_km:
                    anomalies_found += 1
                    OdometerReading.objects.get_or_create(
                        vehicle=vehicle,
                        reading_km=kilometraje,
                        reading_date=row["FECHA"],
                        defaults={
                            "source": OdometerReading.Source.FUEL_FILL,
                            "is_anomaly": True,
                            "notes": (
                                f"Lectura anómala. Anterior: {vehicle.current_odometer_km} km."
                            ),
                        },
                    )
                    continue

                if not FuelFill.objects.filter(
                    vehicle=vehicle,
                    fill_date=row["FECHA"],
                    odometer_km=kilometraje,
                ).exists():
                    fuel_fills.append(
                        FuelFill(
                            vehicle=vehicle,
                            fill_date=row["FECHA"],
                            odometer_km=kilometraje,
                            gallons=row.get("GALONES", 0) or 0,
                            notes=row.get("OBSERVACIONES", ""),
                            source_file=source_filename,
                        )
                    )
                    odometer_readings.append(
                        OdometerReading(
                            vehicle=vehicle,
                            reading_km=kilometraje,
                            reading_date=row["FECHA"],
                            source=OdometerReading.Source.FUEL_FILL,
                        )
                    )
                    vehicle.current_odometer_km = kilometraje
                    vehicles_to_update[vehicle.id] = vehicle
                    new_readings += 1

                processed_count += 1

            except Exception:
                logger.exception("Error procesando fila %s", idx)

        if fuel_fills:
            FuelFill.objects.bulk_create(fuel_fills)
        if odometer_readings:
            OdometerReading.objects.bulk_create(odometer_readings)
        if vehicles_to_update:
            Vehicle.objects.bulk_update(
                list(vehicles_to_update.values()), ["current_odometer_km"]
            )

    logger.info(
        "Archivo procesado: %s registros, %s procesados, %s nuevas lecturas, %s anomalías",
        len(df),
        processed_count,
        new_readings,
        anomalies_found,
    )

    return (
        f"Registros leídos: {len(df)}. Registros procesados: {processed_count}. "
        f"Nuevas lecturas válidas: {new_readings}. Anomalías encontradas: {anomalies_found}."
    )
