"""URL patterns for report endpoints."""

from django.urls import path
from . import views

urlpatterns = [
    path("vehicle-costs/", views.vehicle_costs_report, name="report_vehicle_costs"),
    # --- NUEVA LÍNEA ---
    path(
        "preventive-compliance/",
        views.preventive_compliance_report,
        name="report_preventive_compliance",
    ),
]
