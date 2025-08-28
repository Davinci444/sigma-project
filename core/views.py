# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.contrib import messages
import logging
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
from .forms import FileUploadForm
from io import StringIO

logger = logging.getLogger(__name__)

@user_passes_test(lambda u: u.is_superuser)
def upload_fuel_file_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            if not isinstance(uploaded_file, InMemoryUploadedFile):
                uploaded_file = InMemoryUploadedFile(
                    uploaded_file.file,
                    field_name='file',
                    name=uploaded_file.name,
                    content_type=uploaded_file.content_type,
                    size=uploaded_file.size,
                    charset=uploaded_file.charset,
                )
            if not uploaded_file.name.lower().endswith('.xlsx'):
                messages.error(request, "Solo se permiten archivos con extensión .xlsx")
                return redirect('admin:index')
            try:
                with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp_file:
                    for chunk in uploaded_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file.flush()
                    output = StringIO()
                    call_command('run_daily_jobs', f'--file_path={tmp_file.name}', stdout=output)
                    messages.success(
                        request,
                        f"Archivo '{uploaded_file.name}' procesado. Resumen: {output.getvalue()}",
                    )
            except Exception:
                logger.exception("Error al procesar el archivo de combustible")
                messages.error(request, "Ocurrió un error al procesar el archivo.")
            return redirect('admin:index')
    else:
        form = FileUploadForm()
    return render(request, 'admin/upload_form.html', {
        'form': form, 'title': 'Importar Tanqueos desde Excel',
        'site_header': 'Administración de SIGMA', 'has_permission': True,
    })

# --- NUEVA VISTA PARA EL BOTÓN DE REVISIONES ---
@user_passes_test(lambda u: u.is_superuser)
def run_periodic_checks_view(request):
    try:
        output = StringIO()
        call_command('run_periodic_checks', stdout=output)
        messages.success(request, f"Revisiones Periódicas ejecutadas con éxito. Resumen: {output.getvalue()}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al ejecutar las revisiones: {e}")
    
    # Redirigimos de vuelta a la página principal del admin
    return redirect('admin:index')
