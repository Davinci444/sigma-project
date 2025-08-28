"""URL routes for the workorders application."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderViewSet,
    MaintenancePlanViewSet,
    WorkOrderTaskViewSet,
    WorkOrderPartViewSet,
    schedule_view,  # <- nueva vista
)

router = DefaultRouter()
router.register(r"workorders", WorkOrderViewSet)
router.register(r"plans", MaintenancePlanViewSet)
router.register(r"tasks", WorkOrderTaskViewSet)
router.register(r"parts", WorkOrderPartViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # Página HTML: Programación por fecha
    path("schedule/", schedule_view, name="workorders_schedule"),
]
