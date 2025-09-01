# workorders/urls.py
"""URL routes for the workorders application."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderViewSet,
    MaintenancePlanViewSet,
    WorkOrderTaskViewSet,
    WorkOrderPartViewSet,
    workorder_unified,           # ← NUEVO: editor unificado
    new_preventive,              # ← compat (redirige)
    new_corrective,              # ← compat (redirige)
    edit_tasks,                  # ← compat (redirige)
    schedule_view,               # tu vista de programación
)

# --------- HTML UNIFICADO (PRIMERO para no chocarse con DRF) ---------
urlpatterns = [
    path("workorders/new/", workorder_unified, name="workorders_unified_new"),
    path("workorders/<int:pk>/edit/", workorder_unified, name="workorders_unified_edit"),

    # Compatibilidad con rutas antiguas (redirigen a la unificada)
    path("new/preventive/", new_preventive, name="workorders_new_preventive"),
    path("new/corrective/", new_corrective, name="workorders_new_corrective"),
    path("<int:pk>/tasks/", edit_tasks, name="workorders_edit_tasks"),

    # Página HTML: Programación por fecha (ya la tenías)
    path("schedule/", schedule_view, name="workorders_schedule"),
]

# ---------- API (DRF) DESPUÉS ----------
router = DefaultRouter()
router.register(r"workorders", WorkOrderViewSet)
router.register(r"plans", MaintenancePlanViewSet)
router.register(r"tasks", WorkOrderTaskViewSet)
router.register(r"parts", WorkOrderPartViewSet)

urlpatterns += [ path("", include(router.urls)) ]
