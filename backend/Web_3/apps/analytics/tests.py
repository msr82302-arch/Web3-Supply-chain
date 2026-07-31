# apps/analytics/tests.py
import uuid
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.companies.models import Company, CompanyType
from apps.products.models import Product, ProductCategory
from apps.analytics.models import AIAnalysis, FraudReport, AuditLog
from apps.analytics.service import AnalyticsService
from apps.analytics.selector import AnalyticsSelector
from apps.accounts.models import Role # Imported Role

User = get_user_model()

@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
    'products': None,
    'nft': None,
    'orders': None,
    'shipments': None,
    'notifications': None,
    'analytics': None,
})
class AnalyticsStabilizationTests(TestCase):
    def setUp(self):
        # Dynamically set managed=True for tests so that tables are generated in SQLite
        AIAnalysis._meta.managed = True
        FraudReport._meta.managed = True
        AuditLog._meta.managed = True
        Product._meta.managed = True
        ProductCategory._meta.managed = True
        Company._meta.managed = True
        Role._meta.managed = True

        # FIXED: Provision non-nullable Role instances before user creations
        self.auditor_role = Role.objects.create(role_name="AUDITOR", description="Global Auditor")
        self.manufacturer_role = Role.objects.create(role_name="MANUFACTURER", description="Manufacturer Operator")

        self.auditor_user = User.objects.create_user(
            email="auditor@scm.com",
            password="securepassword123",
            first_name="Global",
            last_name="Auditor",
            role=self.auditor_role # FIXED: Passed role instance
        )
        self.operator_user = User.objects.create_user(
            email="operator@scm.com",
            password="securepassword123",
            first_name="Standard",
            last_name="Operator",
            role=self.manufacturer_role # FIXED: Passed role instance
        )

        self.company_a = Company.objects.create(
            company_name="Company A",
            company_type=CompanyType.MANUFACTURER,
            registration_number="REG-A1",
            tax_number="TAX-A1",
            is_verified=True
        )
        self.company_b = Company.objects.create(
            company_name="Company B",
            company_type=CompanyType.MANUFACTURER,
            registration_number="REG-B1",
            tax_number="TAX-B1",
            is_verified=True
        )

        self.operator_user.company_id = self.company_a.company_id
        self.operator_user.save()

        self.category = ProductCategory.objects.create(
            category_name="Plastics",
            description="Industrial raw plastics"
        )

        self.product_a = Product.objects.create(
            manufacturer_company_id=self.company_a.company_id,
            category=self.category,
            product_name="Product Alpha",
            sku="SKU-A1",
            batch_number="BATCH-A1",
            current_status="MANUFACTURED"
        )
        self.product_b = Product.objects.create(
            manufacturer_company_id=self.company_b.company_id,
            category=self.category,
            product_name="Product Beta",
            sku="SKU-B1",
            batch_number="BATCH-B1",
            current_status="MANUFACTURED"
        )

        self.client = Client()

    def test_tenant_isolation_on_ai_predictions(self):
        # Create AI Analysis for Product B (owned by Company B)
        analysis = AIAnalysis.objects.create(
            product=self.product_b,
            analyzed_by=self.auditor_user.user_id,
            analysis_type="INVENTORY_SCREENS",
            prediction="STABLE",
            confidence_score=Decimal('94.20'),
            model_name="Anomalies_V2",
            model_version="2.0.1"
        )

        # Log in as Company A operator
        self.client.login(username="operator@scm.com", password="securepassword123")
        
        # Verify query filtration excludes competitor results
        visible = AnalyticsSelector.get_visible_analyses(self.operator_user)
        self.assertNotIn(analysis, visible)

    def test_unauthenticated_views_redirect_to_login(self):
        url = reverse('analytics:analytics_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirects to login