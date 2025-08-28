"""URL configuration for the core application."""

from django.urls import path
from . import views

urlpatterns = [
    path("upload-fuel-file/", views.upload_fuel_file_view, name="upload_fuel_file"),
    # --- NUEVA URL ---
    path("run-periodic-checks/", views.run_periodic_checks_view, name="run_periodic_checks"),
]
