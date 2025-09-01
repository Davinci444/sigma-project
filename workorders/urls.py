# workorders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderViewSet, MaintenancePlanViewSet,
    WorkOrderTaskViewSet, WorkOrderPartViewSet,
    schedule_view, new_preventive, new_corrective,
    edit_tasks, add_evidence_url_from_admin
)

router = DefaultRouter()
router.register(r"workorders", WorkOrderViewSet)
router.register(r"plans", MaintenancePlanViewSet)
router.register(r"tasks", WorkOrderTaskViewSet)
router.register(r"parts", WorkOrderPartViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("schedule/", schedule_view, name="workorders_schedule"),

    # HTML management
    path("new/preventive/", new_preventive, name="workorders_new_preventive"),
    path("new/corrective/", new_corrective, name="workorders_new_corrective"),
    path("<int:pk>/tasks/", edit_tasks, name="workorders_edit_tasks"),

    # Hook desde admin para evidencias por URL
    path("<int:pk>/admin/add-evidence-url/", add_evidence_url_from_admin, name="workorders_add_evidence_admin"),
]
