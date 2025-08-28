"""URL configuration del núcleo (core)."""

from django.urls import path
from . import views

urlpatterns = [
    path("upload-fuel-file/", views.upload_fuel_file_view, name="upload_fuel_file"),
    path("run-periodic-checks/", views.run_periodic_checks_view, name="run_periodic_checks"),
    path("seed-taxonomy/", views.seed_taxonomy_view, name="seed_taxonomy"),
]
