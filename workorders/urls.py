# workorders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderViewSet, MaintenancePlanViewSet,
    WorkOrderTaskViewSet, WorkOrderPartViewSet,
    workorder_unified, new_preventive, new_corrective, edit_tasks
)

router = DefaultRouter()
router.register(r"workorders", WorkOrderViewSet)
router.register(r"plans", MaintenancePlanViewSet)
router.register(r"tasks", WorkOrderTaskViewSet)
router.register(r"parts", WorkOrderPartViewSet)

urlpatterns = [
    path("", include(router.urls)),

    # --------- Interfaz unificada ---------
    path("workorders/new/", workorder_unified, name="workorders_unified_new"),
    path("workorders/<int:pk>/edit/", workorder_unified, name="workorders_unified_edit"),

    # --------- Compatibilidad con rutas antiguas (redirigen) ---------
    path("new/preventive/", new_preventive, name="workorders_new_preventive"),
    path("new/corrective/", new_corrective, name="workorders_new_corrective"),
    path("<int:pk>/tasks/", edit_tasks, name="workorders_edit_tasks"),
]
