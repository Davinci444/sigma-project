from django.urls import path
from .views import vehicles_scheduled_view, vehicles_in_workshop_view, vehicles_available_view

urlpatterns = [
    path("scheduled/", vehicles_scheduled_view, name="vehicles_scheduled"),
    path("in-workshop/", vehicles_in_workshop_view, name="vehicles_in_workshop"),
    path("available/", vehicles_available_view, name="vehicles_available"),
]
