from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Zone
from fleet.models import Vehicle
from workorders.models import WorkOrder


@override_settings(MIGRATION_MODULES={"fleet": None})
class QuickCreateNavigationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.client.force_login(self.user)

        self.zone = Zone.objects.create(name="Z1")
        self.vehicle = Vehicle.objects.create(
            plate="ABC123",
            brand="Brand",
            linea="Line",
            modelo=2020,
            vehicle_type=Vehicle.VehicleType.AUTOMOVIL,
            fuel_type=Vehicle.FuelType.DIESEL,
            status=Vehicle.VehicleStatus.ACTIVE,
            current_zone=self.zone,
        )

    def test_quick_create_preserves_querystring(self):
        url = reverse("workorders_unified_new") + "?type=corrective"
        response = self.client.post(url, {"qc_target": "driver"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        self.assertEqual(WorkOrder.objects.count(), 0)

    def test_quick_create_does_not_block_standard_submission(self):
        url = reverse("workorders_unified_new") + "?type=corrective"
        self.client.post(url, {"qc_target": "driver"})
        data = {
            "order_type": WorkOrder.OrderType.CORRECTIVE,
            "vehicle": str(self.vehicle.id),
            "status": WorkOrder.OrderStatus.SCHEDULED,
            "priority": WorkOrder.Priority.MEDIUM,
            "description": "Engine issue",
            "pre_diagnosis": "Initial diagnosis",
            "tasks-TOTAL_FORMS": "0",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(url, data)
        self.assertEqual(WorkOrder.objects.count(), 1)
