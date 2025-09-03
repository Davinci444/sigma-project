from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from fleet.models import Vehicle


class QuickCreateVehicleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.client.force_login(self.user)
        self.url = reverse("workorders_quick_create", args=["vehicle"])

    def test_requires_mandatory_fields(self):
        response = self.client.post(self.url, {"plate": "ABC123"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_creates_vehicle_with_minimum_fields(self):
        payload = {
            "plate": "XYZ987",
            "brand": "Ford",
            "linea": "Fiesta",
            "modelo": 2020,
            "vehicle_type": Vehicle.VehicleType.AUTOMOVIL,
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vehicle.objects.count(), 1)
