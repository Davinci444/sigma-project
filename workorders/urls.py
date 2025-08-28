# workorders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderViewSet,
    MaintenancePlanViewSet,
    WorkOrderTaskViewSet,
    WorkOrderPartViewSet,
)

router = DefaultRouter()
router.register(r"workorders", WorkOrderViewSet)
router.register(r"plans", MaintenancePlanViewSet)
router.register(r"tasks", WorkOrderTaskViewSet)  # Para todas las tareas
router.register(r"parts", WorkOrderPartViewSet)  # Para todos los repuestos

urlpatterns = [
    path("", include(router.urls)),
]
