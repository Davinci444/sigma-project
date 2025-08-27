# reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('vehicle-costs/', views.vehicle_costs_report, name='report_vehicle_costs'),
]
