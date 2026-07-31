# apps/accounts/tests.py
import uuid
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from apps.accounts.models import Company, Role, User
from apps.accounts.serializers import UserCreateSerializer, UserDetailSerializer
from apps.accounts.services import StructuralOnboardingService

User = get_user_model()

# Dynamically set managed=True for tests so that tables are generated in SQLite
User._meta.managed = True
Role._meta.managed = True

# Overrides settings to completely ignore outdated local migrations on test setup
@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
})
class AccountsStabilizationAndHardeningTests(TestCase):
    def setUp(self):
        # 1. Setup multi-tenant Companies using is_verified conformant with active schema
        self.active_company = Company.objects.create(
            company_name="Active Corp",
            company_type="MANUFACTURER",
            registration_number="REG-7718",
            tax_number="TAX-7718",
            is_verified=True
        )
        self.inactive_company = Company.objects.create(
            company_name="Suspended Corp",
            company_type="MANUFACTURER",
            registration_number="REG-9912",
            tax_number="TAX-9912",
            is_verified=False
        )

        # 2. Setup Role states
        self.manufacturer_role = Role.objects.create(role_name="MANUFACTURER", description="Manufacturing Unit")
        self.logistics_role = Role.objects.create(role_name="LOGISTICS", description="Logistics Carrier Unit")

        # 3. Setup Users
        self.active_user = User.objects.create_user(
            email="active@corp.com",
            password="strongpassword123",
            first_name="Active",
            last_name="Operator",
            company=self.active_company,
            role=self.manufacturer_role,
            is_active=True
        )
        self.inactive_user = User.objects.create_user(
            email="inactive@corp.com",
            password="strongpassword123",
            first_name="Inactive",
            last_name="Operator",
            company=self.active_company,
            role=self.manufacturer_role,
            is_active=False
        )
        self.company_inactive_user = User.objects.create_user(
            email="suspended@corp.com",
            password="strongpassword123",
            first_name="Suspended",
            last_name="Operator",
            company=self.inactive_company,
            role=self.manufacturer_role,
            is_active=True
        )

        self.client = Client()

    def test_user_creation_with_email_only(self):
        # Asserts email-based user registration succeeds without username constraints
        new_user = User.objects.create_user(
            email="newoperator@corp.com",
            password="mypassword123",
            first_name="New",
            last_name="Operator",
            role=self.manufacturer_role
        )
        self.assertEqual(new_user.email, "newoperator@corp.com")
        self.assertTrue(new_user.check_password("mypassword123"))

    def test_superuser_creation(self):
        superuser = User.objects.create_superuser(
            email="admin@platform.com",
            password="adminpassword123"
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_active)

    def test_duplicate_email_registration_rejection(self):
        # Asserts duplicate registration throws ValidationError
        with self.assertRaises(ValidationError):
            StructuralOnboardingService.execute_b2b_onboarding({
                'company_name': "Duplicate Test Company",
                'company_type': "MANUFACTURER",
                'registration_number': "REG-D1",
                'tax_number': "TAX-D1",
                'email': "active@corp.com", # Duplicate of setUp user
                'password': "newpassword123",
                'first_name': "Dup",
                'last_name': "User",
                'phone': "123"
            })

    def test_login_flow_with_active_and_inactive_states(self):
        # 1. Login with valid parameters
        response = self.client.post(reverse('accounts:login'), {
            'username': 'active@corp.com',
            'password': 'strongpassword123'
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard

        # 2. Inactive user rejection
        response_inactive = self.client.post(reverse('accounts:login'), {
            'username': 'inactive@corp.com',
            'password': 'strongpassword123'
        })
        self.assertEqual(response_inactive.status_code, 200) # Re-renders login screen with error

        # 3. Inactive company user rejection
        response_suspended = self.client.post(reverse('accounts:login'), {
            'username': 'suspended@corp.com',
            'password': 'strongpassword123'
        })
        self.assertEqual(response_suspended.status_code, 200)

    def test_b2b_onboarding_service_success(self):
        user = StructuralOnboardingService.execute_b2b_onboarding({
            'company_name': "Onboarded SCM Inc",
            'company_type': "LOGISTICS",
            'registration_number': "REG-9901",
            'tax_number': "TAX-9901",
            'email': "logistics_admin@scm.com",
            'password': "carrierpassword123",
            'first_name': "Carrier",
            'last_name': "Admin",
            'phone': "+15550000"
        })
        self.assertEqual(user.email, "logistics_admin@scm.com")
        self.assertEqual(user.company.company_name, "Onboarded SCM Inc")
        self.assertEqual(user.role.role_name, "LOGISTICS")

    def test_password_reset_flow(self):
        # 1. Request recovery token link
        response_req = self.client.post(reverse('accounts:password_reset'), {
            'email': 'active@corp.com'
        })
        self.assertEqual(response_req.status_code, 302) # Redirects to login with success message

        # 2. Assert token validation
        token = default_token_generator.make_token(self.active_user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.active_user.user_id))
        
        confirm_url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response_confirm = self.client.get(confirm_url)
        self.assertEqual(response_confirm.status_code, 200)

        # 3. Submit password override
        response_submit = self.client.post(confirm_url, {
            'password': 'mynewpassword123'
        })
        self.assertEqual(response_submit.status_code, 302) # Redirects to login
        
        self.active_user.refresh_from_db()
        self.assertTrue(self.active_user.check_password("mynewpassword123"))

    def test_user_profile_edit_and_idor_protection(self):
        # Log in as active user
        self.client.login(username="active@corp.com", password="strongpassword123")
        
        profile_url = reverse('accounts:operator_profile', kwargs={'operator_uuid': self.active_user.user_id})
        
        # 1. Valid modification
        response_post = self.client.post(profile_url, {
            'first_name': 'ModifiedName',
            'last_name': 'ModifiedLast',
            'email': 'active@corp.com'
        })
        self.assertEqual(response_post.status_code, 302)
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.first_name, 'ModifiedName')

        # 2. Accessing a profile from a different company is blocked
        intruder_company = Company.objects.create(
            company_name="Competitor", registration_number="REG-0", tax_number="TAX-0"
        )
        intruder_user = User.objects.create_user(
            email="intruder@spy.com",
            password="spy",
            role=self.manufacturer_role,
            company=intruder_company
        )
        
        intruder_profile_url = reverse('accounts:operator_profile', kwargs={'operator_uuid': intruder_user.user_id})
        response_blocked = self.client.get(intruder_profile_url)
        self.assertEqual(response_blocked.status_code, 302) # Redirected away safely