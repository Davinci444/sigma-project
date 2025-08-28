# core/management/commands/run_periodic_checks.py
"""Comando de revisiones periódicas: documentos y mantenimiento preventivo."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from fleet.models import Vehicle
from core.models import Alert
from workorders.models import MaintenancePlan


class Command(BaseCommand):
    help = "Ejecuta revisiones de documentos y mantenimiento preventivo; genera/actualiza alertas."

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        created, updated, closed = 0, 0, 0

        # --- 1) Documentos vencidos / próximos a vencer (SOAT, RTM) ---
        for v in Vehicle.objects.all():
            doc_map = [
                ("SOAT", getattr(v, "soat_due_date", None)),
                ("RTM", getattr(v, "rtm_due_date", None)),
            ]
            for doc_name, due_date in doc_map:
                qs = Alert.objects.filter(
                    alert_type=Alert.AlertType.DOC_EXPIRATION,
                    related_vehicle=v,
                    message__icontains=doc_name,
                    seen=False,
                )
                if due_date:
                    days = (due_date - today).days
                    if days <= 30:
                        severity = (
                            Alert.Severity.CRITICAL if days <= 0 else Alert.Severity.WARNING
                        )
                        estado = "VENCIDO" if days <= 0 else f"vence en {days} día(s)"
                        msg = f"{doc_name} de {v.plate} {estado}. Fecha límite: {due_date}."
                        alert = qs.first()
                        if alert:
                            if alert.severity != severity or alert.message != msg:
                                alert.severity = severity
                                alert.message = msg
                                alert.save(update_fields=["severity", "message"])
                                updated += 1
                        else:
                            Alert.objects.create(
                                alert_type=Alert.AlertType.DOC_EXPIRATION,
                                related_vehicle=v,
                                severity=severity,
                                message=msg,
                                seen=False,
                            )
                            created += 1
                    else:
                        # fuera de ventana (no alertar): cerrar las que estén abiertas
                        closed += qs.update(seen=True)
                else:
                    # sin fecha configurada para ese documento: cerrar cualquier alerta previa
                    closed += qs.update(seen=True)

        # --- 2) Preventivo por kilometraje ---
        # Lógica: base = last_service_km (tu “9”); delta = km_actual - base.
        # Manual define tareas con km_interval (10.000, 20.000, ...).
        # Elegimos la siguiente tarea cuyo km_interval >= delta; si no hay, saltamos al próximo ciclo del menor intervalo.
        plans = (
            MaintenancePlan.objects.filter(is_active=True)
            .select_related("vehicle", "manual")
            .prefetch_related("manual__tasks")
        )

        for plan in plans:
            v = plan.vehicle
            manual = plan.manual
            if not v or not manual:
                continue

            tasks = list(manual.tasks.order_by("km_interval"))
            if not tasks:
                continue

            base_km = plan.last_service_km or 0
            current_km = v.current_odometer_km or 0
            delta = max(0, current_km - base_km)

            # Buscar próxima tarea
            next_task = None
            for t in tasks:
                if t.km_interval >= delta:
                    next_task = t
                    break

            if next_task:
                next_due_km = base_km + next_task.km_interval
                next_desc = next_task.description
            else:
                # ciclo: usamos el menor intervalo como período
                period = tasks[0].km_interval or 10000
                # próximo múltiplo del período
                multiples = (delta // period) + 1
                next_due_km = base_km + multiples * period
                next_desc = f"Ciclo cada {period} km"

            km_to_due = next_due_km - current_km

            qs_prev = Alert.objects.filter(
                alert_type=Alert.AlertType.PREVENTIVE_DUE,
                related_vehicle=v,
                seen=False,
            )

            if km_to_due <= 500:
                severity = (
                    Alert.Severity.CRITICAL if km_to_due <= 0 else Alert.Severity.WARNING
                )
                faltan_txt = f"faltan {max(0, km_to_due)} km" if km_to_due > 0 else "VENCIDO"
                msg = (
                    f"Preventivo para {v.plate}: próximo servicio ({next_desc}) a los "
                    f"{next_due_km} km ({faltan_txt})."
                )
                alert = qs_prev.first()
                if alert:
                    if alert.severity != severity or alert.message != msg:
                        alert.severity = severity
                        alert.message = msg
                        alert.save(update_fields=["severity", "message"])
                        updated += 1
                else:
                    Alert.objects.create(
                        alert_type=Alert.AlertType.PREVENTIVE_DUE,
                        related_vehicle=v,
                        severity=severity,
                        message=msg,
                        seen=False,
                    )
                    created += 1
            else:
                # si ahora está lejos del umbral, cerrar alertas abiertas
                closed += qs_prev.update(seen=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Revisiones completadas. Alertas: +{created} creadas, ~{updated} actualizadas, -{closed} cerradas."
            )
        )
