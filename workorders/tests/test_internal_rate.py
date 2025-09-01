from decimal import Decimal

from django.test import TestCase, override_settings

from fleet.models import Vehicle
from workorders.models import WorkOrder, WorkOrderTask


class WorkOrderCostCalculationTests(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            plate="XYZ123",
            brand="Brand",
            linea="Line",
            modelo=2020,
            vehicle_type=Vehicle.VehicleType.AUTOMOVIL,
        )
        self.work_order = WorkOrder.objects.create(
            vehicle=self.vehicle,
            description="Test order",
        )

    @override_settings(WORKORDER_INTERNAL_RATE=20000)
    def test_recalculate_costs_uses_configured_rate(self):
        WorkOrderTask.objects.create(
            work_order=self.work_order,
            description="Internal task",
            hours_spent=2,
            is_external=False,
        )
        self.work_order.recalculate_costs()
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.labor_cost_internal, Decimal("40000"))
