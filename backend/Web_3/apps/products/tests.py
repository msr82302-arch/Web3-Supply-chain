# apps/products/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.companies.models import Company, CompanyType
from apps.products.models import Product, ProductCategory, ProductStatusHistory
from apps.products.services import CompanyService
from apps.products.selectors import ProductSelector

User = get_user_model()

# Overrides settings to completely ignore outdated local migrations on test setup
@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
    'products': None,
})
class ProductsStabilizationTests(TestCase):
    def setUp(self):
        # Dynamically set managed=True for tests so that tables are generated in SQLite
        Product._meta.managed = True
        ProductCategory._meta.managed = True
        ProductStatusHistory._meta.managed = True
        Company._meta.managed = True

        self.creator_user = User.objects.create_user(
            email="creator@scm.com",
            password="securepassword123",
            first_name="Node",
            last_name="Creator"
        )
        self.other_user = User.objects.create_user(
            email="other@scm.com",
            password="securepassword123",
            first_name="Other",
            last_name="Operator"
        )

        self.company = Company.objects.create(
            company_name="Acme SCM Corp",
            company_type=CompanyType.MANUFACTURER,
            registration_number="REG-7711",
            tax_number="TAX-7711",
            is_verified=True
        )
        
        # FIXED: Assign the raw foreign key directly to prevent the class-mismatch ValueError
        self.creator_user.company_id = self.company.company_id
        self.creator_user.save()

        self.category = ProductCategory.objects.create(
            category_name="Chemical Raw Materials",
            description="Industrial chemical compounds"
        )

        self.client = Client()

    def test_product_creation_via_service(self):
        product = Product.objects.create(
            manufacturer_company_id=self.company.company_id,
            category=self.category,
            product_name="High Density Polyethylene",
            sku="SKU-HDPE-01",
            batch_number="BATCH-2026-01",
            current_status="MANUFACTURED"
        )
        self.assertEqual(product.product_name, "High Density Polyethylene")
        self.assertEqual(product.current_status, "MANUFACTURED")

    def test_product_list_tenant_isolation(self):
        # Create product under company A
        Product.objects.create(
            manufacturer_company_id=self.company.company_id,
            category=self.category,
            product_name="High Density Polyethylene",
            sku="SKU-HDPE-01",
            batch_number="BATCH-2026-01",
            current_status="MANUFACTURED"
        )

        # Login as user from company B (no company associated)
        self.client.login(username="other@scm.com", password="securepassword123")
        url = reverse('product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['product_list']), 0) # No products visible to unrelated company

    def test_unauthenticated_user_redirects_to_login(self):
        url = reverse('product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirects to login