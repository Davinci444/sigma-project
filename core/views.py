"""Views for administrative utilities in the core application."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.contrib import messages
import os
from django.conf import settings
from .forms import FileUploadForm
from io import StringIO


@user_passes_test(lambda u: u.is_superuser)
def upload_fuel_file_view(request):
    """Upload and process an Excel file containing fuel data.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Redirect to the admin index or render the upload form.
    """

    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, "tmp"))
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(filename)
            try:
                output = StringIO()
                call_command("run_daily_jobs", f"--file_path={file_path}", stdout=output)
                messages.success(
                    request,
                    f"Archivo '{filename}' procesado. Resumen: {output.getvalue()}",
                )
            except Exception as e:  # pylint: disable=broad-except
                messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
            finally:
                fs.delete(filename)
            return redirect("admin:index")
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


# --- NUEVA VISTA PARA EL BOTÓN DE REVISIONES ---
@user_passes_test(lambda u: u.is_superuser)
def run_periodic_checks_view(request):
    """Run periodic system checks via management command.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: Redirect to the admin index after execution.
    """

    try:
        output = StringIO()
        call_command("run_periodic_checks", stdout=output)
        messages.success(
            request,
            f"Revisiones Periódicas ejecutadas con éxito. Resumen: {output.getvalue()}",
        )
    except Exception as e:  # pylint: disable=broad-except
        messages.error(request, f"Ocurrió un error al ejecutar las revisiones: {e}")

    # Redirigimos de vuelta a la página principal del admin
    return redirect("admin:index")

