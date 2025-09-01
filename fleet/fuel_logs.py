"""Modelos relacionados con la carga de registros de combustible."""

from django.conf import settings
from django.db import models


class FuelUploadLog(models.Model):
    """Registro de archivos de tanqueos procesados para evitar reprocesos pesados."""

    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, unique=True)
    size_bytes = models.BigIntegerField()
    sheet_name = models.CharField(max_length=100, default="TANQUEOS")
    rows_processed = models.PositiveIntegerField(default=0)
    vehicles_updated = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self) -> str:  # pragma: no cover - string representation
        return (
            f"{self.original_filename} ({self.rows_processed} filas) "
            f"@ {self.processed_at:%Y-%m-%d %H:%M}"
        )
