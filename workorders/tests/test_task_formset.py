from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from fleet.models import Vehicle
from workorders.models import (
    WorkOrder, WorkOrderTask, MaintenanceCategory, MaintenanceSubcategory
)


class TaskFormSetTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.client.force_login(self.user)
        self.vehicle = Vehicle.objects.create(
            plate="ABC123",
            brand="Toyota",
            linea="Corolla",
            modelo=2020,
            vehicle_type=Vehicle.VehicleType.AUTOMOVIL,
        )

    def test_can_add_multiple_tasks(self):
        url = reverse("workorders_unified_new") + "?type=corrective"
        data = {
            "order_type": WorkOrder.OrderType.CORRECTIVE,
            "vehicle": self.vehicle.id,
            "status": WorkOrder.OrderStatus.SCHEDULED,
            "priority": WorkOrder.Priority.MEDIUM,
            "description": "Test order",
            "tasks-TOTAL_FORMS": "2",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-category": "",
            "tasks-0-subcategory": "",
            "tasks-0-description": "Task 1",
            "tasks-0-hours_spent": "1",
            "tasks-0-is_external": "",
            "tasks-0-labor_rate": "",
            "tasks-0-DELETE": "",
            "tasks-1-category": "",
            "tasks-1-subcategory": "",
            "tasks-1-description": "Task 2",
            "tasks-1-hours_spent": "2",
            "tasks-1-is_external": "",
            "tasks-1-labor_rate": "",
            "tasks-1-DELETE": "",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        ot = WorkOrder.objects.get()
        self.assertEqual(ot.tasks.count(), 2)
        self.assertTrue(
            WorkOrderTask.objects.filter(work_order=ot, description="Task 1").exists()
        )
        self.assertTrue(
            WorkOrderTask.objects.filter(work_order=ot, description="Task 2").exists()
        )

    def test_subcategory_must_match_category(self):
        url = reverse("workorders_unified_new") + "?type=corrective"
        cat1 = MaintenanceCategory.objects.create(name="Motor")
        cat2 = MaintenanceCategory.objects.create(name="Frenos")
        sub = MaintenanceSubcategory.objects.create(category=cat2, name="Pastillas")
        data = {
            "order_type": WorkOrder.OrderType.CORRECTIVE,
            "vehicle": self.vehicle.id,
            "status": WorkOrder.OrderStatus.SCHEDULED,
            "priority": WorkOrder.Priority.MEDIUM,
            "description": "Test order",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-category": str(cat1.id),
            "tasks-0-subcategory": str(sub.id),
            "tasks-0-description": "Task invalid",
            "tasks-0-hours_spent": "1",
            "tasks-0-is_external": "",
            "tasks-0-labor_rate": "",
            "tasks-0-DELETE": "",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("subcategory", response.context["task_fs"].forms[0].errors)
        self.assertEqual(WorkOrderTask.objects.count(), 0)
