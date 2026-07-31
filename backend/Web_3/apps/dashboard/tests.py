import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone  # Standard timezone utils

# Import unmanaged models targeted by dashboard selectors [18]
from apps.products.models import Product
from apps.orders.models import Order
from apps.companies.models import Company
from apps.accounts.models import Role, User
from apps.shipments.models import Shipment
from apps.blockchain.models import BlockchainTransaction

User = get_user_model()

class DashboardIntegrationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Establish custom postgres schema in isolated test DB
        # Drop all tables cascadingly to avoid duplicate table collisions [14]
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA IF NOT EXISTS "supply_chain_schema";')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."roles" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."users" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."companies" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."product_categories" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."products" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."orders" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."shipments" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."blockchain_transactions" CASCADE;')
            
            # Re-create the category table directly via SQL [18]
            cursor.execute('CREATE TABLE "supply_chain_schema"."product_categories" (category_id uuid PRIMARY KEY, category_name varchar(100));')

        # 2. Build all unmanaged tables cleanly for tests [18]
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Role)
            schema_editor.create_model(Company)
            schema_editor.create_model(User)
            schema_editor.create_model(Product)
            schema_editor.create_model(Order)
            schema_editor.create_model(Shipment)
            schema_editor.create_model(BlockchainTransaction)
            
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            for model in [Role, Company, User, Product, Order, Shipment, BlockchainTransaction]:
                try:
                    schema_editor.delete_model(model)
                except Exception:
                    pass
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.admin_password = "secure_password_77"
        
        # Instantiate test role
        self.admin_role = Role.objects.create(
            role_id=uuid.uuid4(),
            role_name="Platform Administrator",
            is_active=True
        )

        # Create two valid company nodes to satisfy the orders foreign keys constraints [18]
        self.buyer_company = Company.objects.create(
            company_id=uuid.uuid4(),
            company_name="Buyer Logistics Consortium",
            status="active"
        )
        self.seller_company = Company.objects.create(
            company_id=uuid.uuid4(),
            company_name="Seller Ecosystem Manufacturing",
            status="active"
        )

        # Create admin user without passing non-existent username field [18]
        self.admin_user = User.objects.create_superuser(
            email="admin@saaschain.com",
            password=self.admin_password,
            user_id=uuid.uuid4(),
            role=self.admin_role
        )

        # Seed verified category row directly via SQL to prevent Django model-loader mismatches [18]
        self.category_id = uuid.uuid4()
        with connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO "supply_chain_schema"."product_categories" (category_id, category_name) '
                'VALUES (%s, %s);',
                [str(self.category_id), "Secure NFC Hardware Components"]
            )

        # Seed metrics products with verified PG schema fields [18]
        self.product = Product.objects.create(
            product_id=uuid.uuid4(),
            manufacturer_company_id=self.seller_company.company_id, # Links product to our verified test company [18]
            category_id=self.category_id,                           # Links product to our verified category [18]
            sku="SKU-TEST-9981",
            product_name="Secure NFC Blockchain Assets Tags",
            current_status="pending"
        )

        # Seed metrics orders carrying verified total_amount field and matching company foreign keys [18]
        self.order = Order.objects.create(
            order_id=uuid.uuid4(),
            buyer_company_id=self.buyer_company.company_id,   # Safely references buyer company [18]
            seller_company_id=self.seller_company.company_id,  # Safely references seller company [18]
            order_number="ORD-TEST-1002",
            total_amount=25000.00,
            order_status="confirmed",
            expected_delivery="2026-12-31"
        )

        # Seed metrics shipments carrying verified departure_date and logistics_company_id [18]
        self.shipment = Shipment.objects.create(
            shipment_id=uuid.uuid4(),
            order=self.order,
            logistics_company_id=self.seller_company.company_id,
            shipment_number="SHP-TEST-0045",
            tracking_number="TRK-NEXUS-089",
            shipment_status="in_transit",
            departure_date=timezone.now()
        )

    def test_anonymous_user_is_redirected(self):
        """Verify unauthenticated requests are redirected back to the login gateway."""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_access(self):
        """Verify administrative operators gain entry with verified metrics populated."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('dashboard:home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enterprise SCM Operational Hub")
        self.assertContains(response, "$25,000.00 USD")  # Asserts our seeded order metrics [18]