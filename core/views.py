"""Vistas utilitarias administrativas del núcleo (core)."""

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


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "POST"])
def upload_fuel_file_view(request):
    """Sube y procesa un Excel de tanqueos para actualizar odómetros y registrar la carga."""
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Formulario inválido. Verifique el archivo seleccionado.")
            return redirect("admin:index")

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            messages.error(request, "No se ha seleccionado ningún archivo.")
            return redirect("admin:index")

        if not uploaded_file.name.lower().endswith(".xlsx"):
            messages.error(request, "Solo se permiten archivos con extensión .xlsx")
            return redirect("admin:index")

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp.flush()

            output = StringIO()
            # Comando robusto (idempotente por hash)
            call_command(
                "import_odometer",
                file_path=tmp_path,
                sheet_name="TANQUEOS",
                user_id=request.user.id,
                stdout=output,
            )

            msg = output.getvalue()
            preview = (msg[:600] + "…") if len(msg) > 600 else msg
            messages.success(
                request,
                f"Archivo '{uploaded_file.name}' procesado. Resumen:\n{preview}",
            )

        except Exception as e:
            logger.exception("Error al procesar el archivo de tanqueos")
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
@require_http_methods(["POST", "GET"])
def run_periodic_checks_view(request):
    """Ejecuta revisiones periódicas (comando)."""
    try:
        output = StringIO()
        call_command("run_periodic_checks", stdout=output)

        msg = output.getvalue()
        preview = (msg[:600] + "…") if len(msg) > 600 else msg

        messages.success(
            request,
            f"Revisiones Periódicas ejecutadas con éxito. Resumen:\n{preview}",
        )
    except Exception as e:
        logger.exception("Error al ejecutar las revisiones periódicas")
        messages.error(request, f"Ocurrió un error al ejecutar las revisiones: {e}")

    return redirect("admin:index")


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST", "GET"])
def seed_taxonomy_view(request):
    """Carga/actualiza la taxonomía de categorías y subcategorías para WorkOrderTask."""
    try:
        output = StringIO()
        call_command("seed_maintenance_taxonomy", stdout=output)
        msg = output.getvalue()
        messages.success(request, f"Taxonomía de mantenimiento cargada. {msg}")
    except Exception as e:
        logger.exception("Error al cargar la taxonomía de mantenimiento")
        messages.error(request, f"Ocurrió un error al cargar la taxonomía: {e}")

    return redirect("admin:index")
