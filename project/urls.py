    # project/urls.py (Versión Final)
from django.contrib import admin
from django.urls import path, include # Asegúrate de que 'include' esté importado
from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )

urlpatterns = [
        path('admin/', admin.site.urls),
        
        # --- NUEVA LÍNEA ---
        # Conecta las URLs de nuestra app 'core'
        path('core/', include('core.urls')),

        # --- RUTAS DE LA API ---
        path('api/fleet/', include('fleet.urls')),
        path('api/workorders/', include('workorders.urls')),
        path('api/inventory/', include('inventory.urls')),
        path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]

    # (La personalización del admin se queda igual)
admin.site.site_header = "SIGMA - PETROCONSULTORES S.A.S."
admin.site.site_title = "Portal de Administración SIGMA"
admin.site.index_title = "Bienvenido al portal de gestión de flota"