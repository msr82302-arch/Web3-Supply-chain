# apps/orders/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.companies.models import Company, CompanyType
from apps.products.models import Product, ProductCategory
from apps.orders.models import Order, OrderItem
from apps.orders.services import OrderService

User = get_user_model()

@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
    'products': None,
    'nft': None,
    'orders': None,
})
class OrdersStabilizationTests(TestCase):
    def setUp(self):
        # Dynamically set managed=True for tests so that tables are generated in SQLite
        Order._meta.managed = True
        OrderItem._meta.managed = True
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

        self.buyer_company = Company.objects.create(
            company_name="Buyer Company",
            company_type=CompanyType.BUYER,
            registration_number="REG-BUY1",
            tax_number="TAX-BUY1",
            is_verified=True
        )
        self.seller_company = Company.objects.create(
            company_name="Seller Company",
            company_type=CompanyType.MANUFACTURER,
            registration_number="REG-SEL1",
            tax_number="TAX-SEL1",
            is_verified=True
        )

        self.buyer_user.company_id = self.buyer_company.company_id
        self.buyer_user.save()

        self.seller_user.company_id = self.seller_company.company_id
        self.seller_user.save()

        self.category = ProductCategory.objects.create(
            category_name="Plastics",
            description="Raw plastics"
        )

        self.product = Product.objects.create(
            manufacturer_company_id=self.seller_company.company_id,
            category=self.category,
            product_name="Product Alpha",
            sku="10.50",  # SKU represents unit price in this structure
            batch_number="BATCH-A1",
            current_status="MANUFACTURED"
        )

        self.client = Client()

    def test_order_creation_calculates_subtotal_on_server(self):
        # Verify server-side price computation
        order = OrderService.process_new_invoice(
            order_data={
                'buyer_company': self.buyer_company,
                'seller_company': self.seller_company,
                'order_number': "PO-2026-001",
                'order_status': "PENDING"
            },
            item_payload_list=[{
                'product': self.product,
                'quantity': 100,
                'unit_price': Decimal('10.50')
            }]
        )
        self.assertEqual(order.total_amount, Decimal('1050.00'))
        self.assertEqual(order.items.first().subtotal, Decimal('1050.00'))

    def test_cross_tenant_order_access_denied(self):
        # Create order under buyer company A
        order = Order.objects.create(
            buyer_company=self.buyer_company,
            seller_company=self.seller_company,
            order_number="PO-2026-001",
            total_amount=Decimal('0.00'),
            order_status="PENDING"
        )

        # Login as intruder user
        intruder_company = Company.objects.create(
            company_name="Competitor", registration_number="REG-0", tax_number="TAX-0"
        )
        intruder_user = User.objects.create_user(
            email="intruder@spy.com", password="spy"
        )
        intruder_user.company_id = intruder_company.company_id
        intruder_user.save()

        self.client.login(username="intruder@spy.com", password="spy")
        
        # Detail view must return 404 due to selector boundaries
        url = reverse('order_detail', kwargs={'order_id': order.order_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)