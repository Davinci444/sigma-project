"""Models for the reports application."""

from django.db import models
from django.conf import settings


class FuelUploadLog(models.Model):
    """
    Registro de archivos de tanqueos procesados para evitar reprocesos pesados.
    Se identifica por hash SHA-256 del archivo.
    """
    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, unique=True)
    size_bytes = models.BigIntegerField()
    sheet_name = models.CharField(max_length=100, default="TANQUEOS")
    rows_processed = models.PositiveIntegerField(default=0)
    vehicles_updated = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # 👇 nombre único para evitar choque con cualquier otro FuelUploadLog
        related_name="fuel_upload_logs_reports",
    )

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self) -> str:
        return (
            f"{self.original_filename} (filas={self.rows_processed}, "
            f"act={self.vehicles_updated}) @ {self.processed_at:%Y-%m-%d %H:%M}"
        )
