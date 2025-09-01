"""Tests for the workorders application."""

from django.test import TestCase

from fleet.models import Vehicle
from workorders.models import MaintenanceManual, ManualTask, MaintenancePlan
from workorders.services import calc_next_due


class CalcNextDueTests(TestCase):
    """Tests for the ``calc_next_due`` service."""

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            plate="ABC123",
            brand="Brand",
            model="Model",
            year=2020,
            vehicle_type="Camion",
            fuel_type=Vehicle.FuelType.DIESEL,
        )
        self.manual = MaintenanceManual.objects.create(
            name="Plan Diesel", fuel_type=Vehicle.FuelType.DIESEL
        )
        ManualTask.objects.create(
            manual=self.manual, km_interval=10000, description="Change oil"
        )
        ManualTask.objects.create(
            manual=self.manual, km_interval=20000, description="Change filter"
        )
        ManualTask.objects.create(
            manual=self.manual, km_interval=30000, description="Check belt"
        )

    def test_selects_next_task(self):
        plan = MaintenancePlan.objects.create(
            vehicle=self.vehicle, manual=self.manual, last_service_km=10000
        )
        self.vehicle.current_odometer_km = 15000
        self.vehicle.save()
        next_km, desc = calc_next_due(self.vehicle, plan)
        self.assertEqual(next_km, 20000)
        self.assertEqual(desc, "Change oil")

    def test_cycles_after_last_task(self):
        plan = MaintenancePlan.objects.create(
            vehicle=self.vehicle, manual=self.manual, last_service_km=0
        )
        self.vehicle.current_odometer_km = 35000
        self.vehicle.save()
        next_km, desc = calc_next_due(self.vehicle, plan)
        self.assertEqual(next_km, 40000)
        self.assertEqual(desc, "Ciclo cada 10000 km")
