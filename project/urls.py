# project/urls.py (Versión con Tablero de Control y Reportes)
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# --- Lógica para el Tablero de Control ---
# "Envolvemos" la vista de inicio del admin para añadirle nuestros datos.
original_index = admin.site.index

def custom_index(request, extra_context=None):
    from django.utils import timezone
    from workorders.models import WorkOrder
    
    today = timezone.now()
    
    # Contamos los vehículos que ya ingresaron al taller
    in_workshop_count = WorkOrder.objects.filter(
        check_in_at__isnull=False,
        check_in_at__lte=today
    ).exclude(
        status__in=[WorkOrder.OrderStatus.COMPLETED]
    ).values('vehicle').distinct().count()

    # Contamos los vehículos que tienen una programación a futuro
    scheduled_count = WorkOrder.objects.filter(
        status=WorkOrder.OrderStatus.SCHEDULED,
        scheduled_start__isnull=False,
        scheduled_start__gt=today
    ).values('vehicle').distinct().count()

    if extra_context is None:
        extra_context = {}
    
    # Pasamos los contadores a la plantilla
    extra_context['in_workshop_count'] = in_workshop_count
    extra_context['scheduled_count'] = scheduled_count
    
    return original_index(request, extra_context)

admin.site.index = custom_index
# --- FIN DE LA NUEVA LÓGICA ---


urlpatterns = [
    # NUEVO: rutas HTML de OT dentro del admin (ANTES del include del admin)
    path('admin/workorders/', include('workorders.admin_urls')),

    path('admin/', admin.site.urls),
    
    # URLs de nuestras aplicaciones principales
    path('core/', include('core.urls')),
    path('reports/', include('reports.urls')),

    # --- RUTAS DE LA API ---
    path('api/fleet/', include('fleet.urls')),
    path('api/workorders/', include('workorders.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/users/', include('users.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# --- PERSONALIZACIÓN DEL PANEL DE ADMINISTRACIÓN ---
admin.site.site_header = "SIGMA - PETROCONSULTORES S.A.S."
admin.site.site_title = "Portal de Administración SIGMA"
admin.site.index_title = "Bienvenido al portal de gestión de flota"
