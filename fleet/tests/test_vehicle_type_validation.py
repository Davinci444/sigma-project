from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase


class VehicleTypeValidationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("vehicle-list")
        self.base_payload = {
            "plate": "TEST123",
            "brand": "Test",
            "linea": "Model",
            "modelo": 2024,
        }

    def test_invalid_vehicle_type_returns_400(self):
        payload = {**self.base_payload, "vehicle_type": "INVALID"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle_type", response.data)

    def test_missing_vehicle_type_returns_400(self):
        response = self.client.post(self.url, self.base_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle_type", response.data)
