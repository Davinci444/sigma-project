"""Models for the reports application."""

from django.db import models
from django.conf import settings


class FuelUploadLog(models.Model):
    """Registro de archivos procesados, identificado por el hash SHA-256 del archivo."""
    original_filename = models.CharField(
        max_length=255,
        help_text="Nombre original del archivo subido.",
    )
    sha256 = models.CharField(
        max_length=64,
        unique=True,
        help_text="Hash SHA-256 del archivo procesado.",
    )
    size_bytes = models.BigIntegerField(
        help_text="Tamaño del archivo en bytes.",
    )
    sheet_name = models.CharField(
        max_length=100,
        default="TANQUEOS",
        help_text="Nombre de la hoja del archivo procesada.",
    )
    rows_processed = models.PositiveIntegerField(
        default=0,
        help_text="Número de filas leídas del archivo.",
    )
    vehicles_updated = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad de vehículos actualizados.",
    )
    processed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de procesamiento.",
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # 👇 nombre único para evitar choque con cualquier otro FuelUploadLog
        related_name="fuel_upload_logs_reports",
        help_text="Usuario que procesó el archivo.",
    )

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self) -> str:
        return (
            f"{self.original_filename} (filas={self.rows_processed}, "
            f"act={self.vehicles_updated}) @ {self.processed_at:%Y-%m-%d %H:%M}"
        )
