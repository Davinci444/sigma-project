"""URL routes for the fleet application."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, vehicles_in_repair_view

router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # Página HTML: Vehículos en Taller
    path("garage/", vehicles_in_repair_view, name="vehicles_in_repair"),
]
