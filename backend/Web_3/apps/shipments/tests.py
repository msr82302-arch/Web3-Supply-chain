# apps/shipments/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.companies.models import Company, CompanyType
from apps.products.models import Product, ProductCategory
from apps.orders.models import Order
from apps.shipments.models import Shipment, ShipmentTracking
from apps.shipments.service import ShipmentService

User = get_user_model()

@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
    'products': None,
    'nft': None,
    'orders': None,
    'shipments': None,
})
class ShipmentsStabilizationTests(TestCase):
    def setUp(self):
        # Dynamically set managed=True for tests so that tables are generated in SQLite
        Shipment._meta.managed = True
        ShipmentTracking._meta.managed = True
        Order._meta.managed = True
        Product._meta.managed = True
        ProductCategory._meta.managed = True
        Company._meta.managed = True

        self.buyer_user = User.objects.create_user(
            email="buyer@scm.com",
            password="securepassword123",
            first_name="Buyer",
            last_name="Node"
        )
        self.seller_user = User.objects.create_user(
            email="seller@scm.com",
            password="securepassword123",
            first_name="Seller",
            last_name="Node"
        )
        self.carrier_user = User.objects.create_user(
            email="carrier@logistics.com",
            password="securepassword123",
            first_name="Carrier",
            last_name="Node"
        )

        self.buyer_company = Company.objects.create(
            company_name="Buyer Company",
            company_type=CompanyType.BUYER,
            registration_number="REG-BY1",
            tax_number="TAX-BY1",
            is_verified=True
        )
        self.seller_company = Company.objects.create(
            company_name="Seller Company",
            company_type=CompanyType.MANUFACTURER,
            registration_number="REG-SL1",
            tax_number="TAX-SL1",
            is_verified=True
        )
        self.carrier_company = Company.objects.create(
            company_name="Logistics Partner",
            company_type=CompanyType.LOGISTICS_PROVIDER,
            registration_number="REG-LOG1",
            tax_number="TAX-LOG1",
            is_verified=True
        )

        self.buyer_user.company_id = self.buyer_company.company_id
        self.buyer_user.save()

        self.seller_user.company_id = self.seller_company.company_id
        self.seller_user.save()

        self.carrier_user.company_id = self.carrier_company.company_id
        self.carrier_user.save()

        self.order = Order.objects.create(
            buyer_company=self.buyer_company,
            seller_company=self.seller_company,
            order_number="PO-2026-9912",
            total_amount=Decimal('0.00'),
            order_status="CONFIRMED"
        )

        self.client = Client()

    def test_shipment_creation_success(self):
        shipment = ShipmentService.initiate_shipment({
            'order': self.order,
            'logistics_company': self.carrier_company,
            'shipment_number': "SM-2026-101",
            'tracking_number': "TRK-00921"
        })
        self.assertEqual(shipment.shipment_number, "SM-2026-101")
        self.assertEqual(shipment.shipment_status, "MANIFEST_CREATED")

    def test_telemetry_append_gps_ping_precision(self):
        shipment = ShipmentService.initiate_shipment({
            'order': self.order,
            'logistics_company': self.carrier_company,
            'shipment_number': "SM-2026-101"
        })

        tracking = ShipmentService.append_gps_ping(shipment, {
            'latitude': Decimal('50.1109000'),
            'longitude': Decimal('8.6821000'),
            'location': "Frankfurt Depot",
            'tracking_status': "IN_TRANSIT"
        })
        self.assertEqual(tracking.location, "Frankfurt Depot")
        self.assertEqual(tracking.latitude, Decimal('50.1109000'))

    def test_unauthorized_telemetry_logging_rejection(self):
        # Create shipment
        shipment = ShipmentService.initiate_shipment({
            'order': self.order,
            'logistics_company': self.carrier_company,
            'shipment_number': "SM-2026-101"
        })

        # Login as seller (should not be allowed to log GPS waypoints)
        self.client.login(username="seller@scm.com", password="securepassword123")
        url = reverse('shipment-api-detail', kwargs={'pk': shipment.shipment_id}) + 'log-telemetry/'
        
        response = self.client.post(url, {
            'latitude': 50.1109,
            'longitude': 8.6821,
            'location': "Frankfurt Depot",
            'tracking_status': "IN_TRANSIT"
        })
        self.assertEqual(response.status_code, 403) # Rejects with Forbidden