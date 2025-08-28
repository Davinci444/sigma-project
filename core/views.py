"""Views for administrative utilities in the core application."""

import logging
import os
import tempfile
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.management import call_command

from .forms import FileUploadForm

logger = logging.getLogger(__name__)

# MIME types válidos para .xlsx (algunos navegadores varían)
_XLSX_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",  # a veces llega así
}


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "POST"])
def upload_fuel_file_view(request):
    """Upload and process an Excel file containing fuel data (.xlsx only)."""
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Formulario inválido. Verifique el archivo seleccionado.")
            return redirect("admin:index")

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            messages.error(request, "No se ha seleccionado ningún archivo.")
            return redirect("admin:index")

        # Validación por extensión
        if not uploaded_file.name.lower().endswith(".xlsx"):
            messages.error(request, "Solo se permiten archivos con extensión .xlsx")
            return redirect("admin:index")

        # Validación (best-effort) por MIME
        if uploaded_file.content_type and uploaded_file.content_type not in _XLSX_MIMES:
            logger.warning(
                "Tipo de contenido inesperado para .xlsx: %s (archivo: %s)",
                uploaded_file.content_type, uploaded_file.name
            )

        tmp_path = None
        try:
            # En Windows es más seguro delete=False; lo borramos manualmente en finally
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file.flush()

            # Ejecutar el management command con kwargs (NO pasar '--file_path=...')
            output = StringIO()
            call_command("run_daily_jobs", file_path=tmp_path, stdout=output)

            # Evitar mensajes gigantes en el admin
            msg = output.getvalue()
            preview = (msg[:600] + "…") if len(msg) > 600 else msg

            messages.success(
                request,
                f"Archivo '{uploaded_file.name}' procesado correctamente. Resumen:\n{preview}",
            )
        except Exception as e:
            logger.exception("Error al procesar el archivo de combustible")
            messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    logger.warning("No se pudo eliminar el temporal: %s", tmp_path)

        return redirect("admin:index")

    # GET
    form = FileUploadForm()
    return render(
        request,
        "admin/upload_form.html",
        {
            "form": form,
            "title": "Importar Tanqueos desde Excel",
            "site_header": "Administración de SIGMA",
            "has_permission": True,
        },
    )


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST", "GET"])  # si deseas, deja solo POST
def run_periodic_checks_view(request):
    """Run periodic system checks via management command."""
    try:
        output = StringIO()
        call_command("run_periodic_checks", stdout=output)

        msg = output.getvalue()
        preview = (msg[:600] + "…") if len(msg) > 600 else msg

        messages.success(
            request,
            f"Revisiones periódicas ejecutadas con éxito. Resumen:\n{preview}",
        )
    except Exception as e:
        logger.exception("Error al ejecutar las revisiones periódicas")
        messages.error(request, f"Ocurrió un error al ejecutar las revisiones: {e}")

    return redirect("admin:index")
