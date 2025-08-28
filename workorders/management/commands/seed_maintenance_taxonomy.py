# workorders/management/commands/seed_maintenance_taxonomy.py
"""
Semilla de taxonomía de mantenimiento (Categorías y Subcategorías) para usar en WorkOrderTask.

Idempotente: si la categoría/subcategoría ya existe, no la duplica.
"""

from django.core.management.base import BaseCommand
from workorders.models import MaintenanceCategory, MaintenanceSubcategory


TAXONOMIA = {
    # 1) Motor
    "Motor - Lubricación": [
        "Aceite de motor",
        "Filtro de aceite",
        "Fugas de lubricación",
        "Análisis de aceite (TBN/viscosidad/metales)",
    ],
    "Motor - Refrigeración": [
        "Refrigerante (mezcla/PH/°Brix)",
        "Radiador (limpieza/rectificación)",
        "Mangueras/abrazaderas",
        "Termostato",
        "Bomba de agua",
        "Tapón/presión del sistema",
    ],
    "Motor - Admisión y Escape": [
        "Filtro de aire (inspección/cambio)",
        "Cuerpo de aceleración",
        "Múltiple/silenciador (fugas/soportes)",
        "Sensor MAF/MAP",
    ],
    "Motor - Encendido (Gasolina)": [
        "Bujías (calibración y cambio)",
        "Bobinas/cables",
    ],
    "Motor - Post-tratamiento (Diésel)": [
        "EGR",
        "DPF (regeneración/limpieza)",
        "SCR/AdBlue (inyección/depósito/bomba)",
        "Sensores NOx",
    ],

    # 2) Sistema de combustible
    "Combustible - Diésel": [
        "Filtro primario",
        "Filtro secundario",
        "Bomba alta presión/riel común",
        "Inyectores (prueba/limpieza/calibración)",
        "Líneas y retornos",
    ],
    "Combustible - Gasolina": [
        "Bomba/regulador (presión)",
        "Filtro de combustible",
        "Inyectores (multipunto/GDI)",
        "Cuerpo de aceleración",
        "Líneas y retorno",
    ],

    # 3) Transmisión y tracción
    "Transmisión - Manual": [
        "Embrague (kit completo)",
        "Cilindro maestro/esclavo",
        "Caja (aceite/fugas)",
    ],
    "Transmisión - Automática/AT/AMT/CVT": [
        "ATF y filtro",
        "Solenoides",
        "Enfriador",
    ],
    "Ejes y Diferenciales": [
        "Diferencial (aceite/backlash)",
        "Homocinéticas/crucetas",
        "Retenes/fugas",
    ],

    # 4) Frenos
    "Frenos - Hidráulico": [
        "Pastillas/discos",
        "Líquido de frenos (DOT/%humedad)",
        "Mangueras/cálipers",
    ],
    "Frenos - Neumático": [
        "Cámaras/válvulas",
        "Compresor/secador",
        "Líneas/fugas",
    ],

    # 5) Suspensión y dirección
    "Suspensión": [
        "Amortiguadores",
        "Bujes/soportes",
        "Ballestas",
        "Estabilizadora",
    ],
    "Dirección": [
        "Cremallera/caña",
        "Terminales/axiales",
        "Alineación/balanceo",
    ],

    # 6) Neumáticos
    "Neumáticos": [
        "Rotación",
        "Calibración/presión",
        "Reparación (vulcanizado/parche)",
        "Cambio de llanta",
    ],

    # 7) Eléctrico / Electrónico
    "Eléctrico - Batería y Carga": [
        "Batería (prueba CCA/cambio)",
        "Alternador (carga)",
        "Motor de arranque",
    ],
    "Eléctrico - Sensores/ECU/OBD": [
        "Diagnóstico OBD (lectura/borrado)",
        "Sensores críticos (MAP/MAF/CKP/CMP/O2)",
        "Cableados/conectores",
    ],

    # 8) Climatización (A/C)
    "Climatización (A/C)": [
        "Recuperación/vacío/carga gas",
        "Compresor/condensador/evaporador",
        "Fugas (UV/booster)",
        "Filtro de cabina",
    ],

    # 9) Carrocería / Interior
    "Carrocería/Interior": [
        "Puertas/cerraduras/bisagras",
        "Vidrios/levas",
        "Asientos/cinturones",
        "Sellos/ruidos/parásitos",
    ],

    # 10) Seguridad / Dotación
    "Seguridad/Dotación": [
        "Extintor/botiquín/triángulos",
        "Airbags/pretensores (SRS)",
        "Luces externas (faro/stop/direccional)",
    ],

    # 11) Regulatorio
    "Regulatorio": [
        "SOAT/RTM/Seguros",
        "Prueba de emisiones/opacidad",
        "Inspección general",
    ],

    # 12) Telemetría / Sensores de combustible
    "Telemetría/Sensores": [
        "GPS/odómetro",
        "Aforo de tanque",
        "Sondas de combustible",
    ],
}


class Command(BaseCommand):
    help = "Crea categorías y subcategorías de mantenimiento para alimentar WorkOrderTask."

    def handle(self, *args, **kwargs):
        creadas_cat = 0
        creadas_sub = 0

        for nombre_cat, subcats in TAXONOMIA.items():
            categoria, creada = MaintenanceCategory.objects.get_or_create(
                name=nombre_cat,
                defaults={"description": ""},
            )
            if creada:
                creadas_cat += 1

            for nombre_sub in subcats:
                _, creada_s = MaintenanceSubcategory.objects.get_or_create(
                    category=categoria,
                    name=nombre_sub,
                    defaults={"description": ""},
                )
                if creada_s:
                    creadas_sub += 1

        self.stdout.write(self.style.SUCCESS(
            f"Taxonomía creada/actualizada. Categorías nuevas: {creadas_cat} | Subcategorías nuevas: {creadas_sub}"
        ))
