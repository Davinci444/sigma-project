# project/urls.py (Versión con API)
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- RUTAS DE LA API ---
    # Le decimos a Django que cualquier URL que empiece con 'api/fleet/'
    # la busque en el archivo urls.py de la app fleet.
    path('api/fleet/', include('fleet.urls')),
    path('api/workorders/', include('workorders.urls')),
    path('api/inventory/', include('inventory.urls')),

    # --- RUTAS DE AUTENTICACIÓN DE LA API ---
    # Estas son las URLs para iniciar sesión y refrescar el token.
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# --- PERSONALIZACIÓN DEL PANEL DE ADMINISTRACIÓN ---
admin.site.site_header = "SIGMA - PETROCONSULTORES S.A.S."
admin.site.site_title = "Portal de Administración SIGMA"
admin.site.index_title = "Bienvenido al portal de gestión de flota"