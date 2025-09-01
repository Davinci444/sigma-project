# workorders/urls.py
"""URL routes for the workorders application."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkOrderViewSet,
    MaintenancePlanViewSet,
    WorkOrderTaskViewSet,
    WorkOrderPartViewSet,
    MaintenanceCategoryViewSet,
    MaintenanceSubcategoryViewSet,
    workorder_unified,
    quick_create,
    new_preventive, new_corrective, edit_tasks,
    schedule_view,
)

# --------- HTML UNIFICADO (no admin; compatibilidad) ---------
urlpatterns = [
    path("workorders/qc/<str:target>/", quick_create, name="workorders_quick_create"),
    path("workorders/new/", workorder_unified, name="workorders_unified_new"),
    path("workorders/<int:pk>/edit/", workorder_unified, name="workorders_unified_edit"),

    path("new/preventive/", new_preventive, name="workorders_new_preventive"),
    path("new/corrective/", new_corrective, name="workorders_new_corrective"),
    path("<int:pk>/tasks/", edit_tasks, name="workorders_edit_tasks"),

    path("schedule/", schedule_view, name="workorders_schedule"),
]

# ---------- API (DRF) ----------
router = DefaultRouter()
router.register(r"workorders", WorkOrderViewSet)
router.register(r"plans", MaintenancePlanViewSet)
router.register(r"tasks", WorkOrderTaskViewSet)
router.register(r"parts", WorkOrderPartViewSet)
router.register(r"categories", MaintenanceCategoryViewSet, basename="category")
router.register(r"subcategories", MaintenanceSubcategoryViewSet, basename="subcategory")

urlpatterns += [ path("", include(router.urls)) ]
