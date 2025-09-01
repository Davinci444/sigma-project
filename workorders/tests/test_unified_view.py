"""Tests for the workorders application."""

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Zone
from fleet.models import Vehicle
from workorders.models import WorkOrder
from workorders.forms import WorkOrderUnifiedForm


@override_settings(MIGRATION_MODULES={"fleet": None})
class WorkOrderUnifiedViewTests(TestCase):
    """Integration tests for the unified work order view."""

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

    def test_corrective_order_saves_diagnostic(self):
        """Creating a corrective OT should persist the diagnostic field."""
        url = reverse("workorders_unified_new") + "?type=corrective"
        data = {
            "vehicle": str(self.vehicle.id),
            "order_type": WorkOrder.OrderType.CORRECTIVE,
            "status": WorkOrder.OrderStatus.SCHEDULED,
            "priority": WorkOrder.Priority.MEDIUM,
            "description": "Engine issue",
            "pre_diagnosis": "Initial diagnosis",
            # Formset management data without tasks
            "tasks-TOTAL_FORMS": "0",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        wo = WorkOrder.objects.get()
        self.assertEqual(wo.order_type, WorkOrder.OrderType.CORRECTIVE)
        self.assertEqual(wo.pre_diagnosis, "Initial diagnosis")

    def test_edit_corrective_to_preventive_clears_diagnostic_fields(self):
        """Editing a corrective OT to preventive should clear diagnostic fields."""
        from workorders.models import ProbableCause

        cause = ProbableCause.objects.create(name="Fallo")
        wo = WorkOrder.objects.create(
            vehicle=self.vehicle,
            description="Engine issue",
            order_type=WorkOrder.OrderType.CORRECTIVE,
            pre_diagnosis="Initial diagnosis",
            failure_origin=WorkOrder.FailureOrigin.OTHER,
            severity=WorkOrder.Severity.HIGH,
        )
        wo.probable_causes.add(cause)

        url = reverse("workorders_unified_edit", args=[wo.id])
        data = {
            "vehicle": str(self.vehicle.id),
            "order_type": WorkOrder.OrderType.PREVENTIVE,
            "status": WorkOrder.OrderStatus.SCHEDULED,
            "priority": WorkOrder.Priority.MEDIUM,
            "description": "Engine issue",
            "tasks-TOTAL_FORMS": "0",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        wo.refresh_from_db()
        self.assertEqual(wo.order_type, WorkOrder.OrderType.PREVENTIVE)
        self.assertEqual(wo.pre_diagnosis, "")
        self.assertIsNone(wo.failure_origin)
        self.assertIsNone(wo.severity)
        self.assertEqual(wo.probable_causes.count(), 0)

    def test_can_create_in_progress_order(self):
        """IN_PROGRESS should be a valid status option."""
        url = reverse("workorders_unified_new") + "?type=corrective"
        data = {
            "vehicle": str(self.vehicle.id),
            "order_type": WorkOrder.OrderType.CORRECTIVE,
            "status": WorkOrder.OrderStatus.IN_PROGRESS,
            "priority": WorkOrder.Priority.MEDIUM,
            "description": "Testing IN_PROGRESS status",
            "tasks-TOTAL_FORMS": "0",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        wo = WorkOrder.objects.get(description="Testing IN_PROGRESS status")
        self.assertEqual(wo.status, WorkOrder.OrderStatus.IN_PROGRESS)

    def test_form_includes_in_progress_choice(self):
        form = WorkOrderUnifiedForm()
        choices = [c[0] for c in form.fields["status"].choices]
        self.assertIn(WorkOrder.OrderStatus.IN_PROGRESS, choices)

    def test_breadcrumb_links_change_with_route(self):
        admin_url = reverse("workorders_admin_new")
        ext_url = reverse("workorders_unified_new")

        resp_admin = self.client.get(admin_url)
        self.assertContains(resp_admin, f'href="{reverse("admin:index")}"')

        resp_ext = self.client.get(ext_url)
        self.assertContains(resp_ext, f'href="{ext_url}"')

    def test_bottom_button_links_change_with_route(self):
        wo = WorkOrder.objects.create(vehicle=self.vehicle, description="Test")

        admin_edit = reverse("workorders_admin_edit", args=[wo.id])
        ext_edit = reverse("workorders_unified_edit", args=[wo.id])

        resp_admin = self.client.get(admin_edit)
        self.assertContains(resp_admin, f'href="{reverse("admin:index")}"')

        resp_ext = self.client.get(ext_edit)
        self.assertContains(resp_ext, f'href="{ext_edit}"')
