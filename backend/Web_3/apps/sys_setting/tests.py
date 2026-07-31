from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient  # Native DRF testing client [15]
from .models import SystemSetting
import uuid

User = get_user_model()

class SystemSettingsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Dynamically ensure the custom schema exists in your isolated test database
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA IF NOT EXISTS "supply_chain_schema";')
        
        # 2. Instruct the SchemaEditor to build the unmanaged table for the duration of this class
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(SystemSetting)
            
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # 3. Clean up the unmanaged table after the tests in this class finish running
        with connection.schema_editor() as schema_editor:
            try:
                schema_editor.delete_model(SystemSetting)
            except Exception:
                pass
        super().tearDownClass()

    def setUp(self):
        # Initialize native REST Framework APIClient to test template & API views cleanly [15]
        self.client = APIClient()
        self.admin_password = "secure_password_77"
        
        # Instantiate and save the superuser with the UUID primary key [2]
        self.admin_user = User.objects.create_superuser(
            email="admin@saaschain.com",
            password=self.admin_password,
            user_id=uuid.uuid4()
        )
        
        # Explicitly assign staff credentials for verification logic
        self.admin_user.is_staff = True
        self.admin_user.save()

        # Seed global config record
        self.setting = SystemSetting.objects.create(
            application_name='Web3 Supply Chain SaaS',
            blockchain_network='Ethereum',
            enable_blockchain=True
        )

    def test_anonymous_access_denied(self):
        """Verify anonymous requests are blocked from viewing the main settings panel."""
        response = self.client.get(reverse('sys_setting:settings-dashboard'))
        self.assertEqual(response.status_code, 302)  # Verifies login redirect

    def test_authenticated_admin_access(self):
        """Verify logged-in administrative accounts can access the settings interface."""
        self.client.force_login(self.admin_user)  # Session login for Django views
        response = self.client.get(reverse('sys_setting:settings-dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_put_rest_apis_with_validation_check(self):
        """Verify update endpoints accept valid payloads and return wrapped formats."""
        self.client.force_authenticate(user=self.admin_user)  # DRF Native Authentication [15]
        payload = {
            "application_name": "Updated Web3 Supply Chain SaaS Node",
            "currency": "EUR"
        }
        response = self.client.put(
            reverse('sys_setting:api-general'),
            data=payload,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')