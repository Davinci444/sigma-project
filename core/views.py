"""Views for administrative utilities in the core application."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.contrib import messages
import logging
import tempfile
from .forms import FileUploadForm
from io import StringIO

logger = logging.getLogger(__name__)

@user_passes_test(lambda u: u.is_superuser)
def upload_fuel_file_view(request):
    """Upload and process an Excel file containing fuel data."""

    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                messages.error(request, "No se ha seleccionado ningún archivo.")
                return redirect('admin:index')
            if not uploaded_file.name.lower().endswith('.xlsx'):
                messages.error(request, "Solo se permiten archivos con extensión .xlsx")
                return redirect('admin:index')
            try:
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                    for chunk in uploaded_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file.flush()
                    output = StringIO()
                    call_command('run_daily_jobs', f'--file_path={tmp_file.name}', stdout=output)
                    messages.success(
                        request,
                        f"Archivo '{uploaded_file.name}' procesado. Resumen: {output.getvalue()}",
                    )
            except Exception as e:
                logger.exception("Error al procesar el archivo de combustible")
                messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
            return redirect('admin:index')
        else:
            messages.error(request, "Formulario inválido. Verifique el archivo seleccionado.")
            return redirect('admin:index')
    else:
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
def run_periodic_checks_view(request):
    """Run periodic system checks via management command."""

    try:
        output = StringIO()
        call_command("run_periodic_checks", stdout=output)
        messages.success(
            request,
            f"Revisiones Periódicas ejecutadas con éxito. Resumen: {output.getvalue()}",
        )
    except Exception as e:
        logger.exception("Error al ejecutar las revisiones periódicas")
        messages.error(request, f"Ocurrió un error al ejecutar las revisiones: {e}")

    return redirect('admin:index')
