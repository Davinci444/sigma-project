# project/urls.py (Versión Completa y Corregida)

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# --- PERSONALIZACIÓN DEL PANEL DE ADMINISTRACIÓN ---
# Aquí es donde personalizamos los títulos que se ven en la página.
admin.site.site_header = "SIGMA - PETROCONSULTORES S.A.S."
admin.site.site_title = "Portal de Administración SIGMA"
admin.site.index_title = "Bienvenido al portal de gestión de flota"
