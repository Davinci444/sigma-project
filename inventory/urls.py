# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartViewSet, SupplierViewSet

router = DefaultRouter()
router.register(r"parts", PartViewSet)
router.register(r"suppliers", SupplierViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
