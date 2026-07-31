# apps/companies/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.companies.models import Company, CompanyType, CompanyStatus
from apps.companies.service import CompanyService
from apps.companies.selectors import CompanySelector

User = get_user_model()

# Overrides settings to completely ignore outdated local migrations on test setup
@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
})
class CompaniesStabilizationTests(TestCase):
    def setUp(self):
        # Dynamically set managed=True for tests so that tables are generated in SQLite
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
        self.client = Client()

    def test_company_creation_via_service(self):
        company = CompanyService.create_company_with_channels(
            company_data={
                'company_name': "Acme Manufacturing",
                'company_type': CompanyType.MANUFACTURER,
                'registration_number': "REG-110022",
                'tax_number': "TAX-110022",
                'email': "info@acme.com"
            },
            creator_user_id=self.creator_user.user_id,
            addresses_data=[]
        )
        self.assertEqual(company.company_name, "Acme Manufacturing")
        self.assertFalse(company.is_verified)
        self.assertEqual(company.status, CompanyStatus.PENDING)

    def test_onboarding_requires_valid_user_identity(self):
        with self.assertRaises(ValidationError):
            CompanyService.create_company_with_channels(
                company_data={
                    'company_name': "Acme Manufacturing",
                    'company_type': CompanyType.MANUFACTURER,
                    'registration_number': "REG-110022",
                    'tax_number': "TAX-110022"
                },
                creator_user_id=None,
                addresses_data=[]
            )

    def test_company_list_html_view_requires_login(self):
        url = reverse('company_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirects to login

    def test_company_list_html_view_success_when_authenticated(self):
        self.client.login(username="creator@scm.com", password="securepassword123")
        url = reverse('company_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)