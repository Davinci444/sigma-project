# workorders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkOrderViewSet, MaintenancePlanViewSet

router = DefaultRouter()
router.register(r'workorders', WorkOrderViewSet)
router.register(r'plans', MaintenancePlanViewSet)

urlpatterns = [
    path('', include(router.urls)),
]