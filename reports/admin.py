"""Admin configuration for reports."""

from django.contrib import admin
from .models import FuelUploadLog


@admin.register(FuelUploadLog)
class FuelUploadLogAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "processed_at",
        "vehicles_updated",
        "rows_processed",
        "size_bytes",
    )
    search_fields = ("original_filename", "sha256")
    readonly_fields = ("processed_at",)
    ordering = ("-processed_at",)