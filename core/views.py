    # core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.contrib import messages
import os
from django.conf import settings
from .forms import FileUploadForm

    # Solo los superusuarios pueden acceder a esta vista
@user_passes_test(lambda u: u.is_superuser)
def upload_fuel_file_view(request):
        if request.method == 'POST':
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES['file']
                # Creamos una carpeta temporal 'tmp' para guardar el archivo
                fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'tmp'))
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(filename)

                try:
                    # Llamamos a nuestro comando pasándole la ruta del archivo
                    # Usamos StringIO para capturar la salida del comando
                    from io import StringIO
                    output = StringIO()
                    call_command('run_daily_jobs', f'--file_path={file_path}', stdout=output)
                    
                    # Mostramos la salida del comando como un mensaje de éxito
                    messages.success(request, f"Archivo '{filename}' procesado. Resumen: {output.getvalue()}")

                except Exception as e:
                    messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
                
                finally:
                    # Borramos el archivo temporal después de usarlo
                    fs.delete(filename)
                
                return redirect('admin:index') # Redirigir a la página principal del admin
        else:
            form = FileUploadForm()
        
        return render(request, 'admin/upload_form.html', {
            'form': form,
            'title': 'Importar Tanqueos desde Excel',
            'site_header': 'Administración de SIGMA',
            'has_permission': True,
        })