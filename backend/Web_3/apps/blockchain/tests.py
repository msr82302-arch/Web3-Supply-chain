import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient  # Native DRF testing client [15]
from apps.blockchain.models import Wallet, BlockchainTransaction, OwnershipHistory
from apps.blockchain.service import BlockchainService

User = get_user_model()

class BlockchainInfrastructureTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Ensure the custom schema exists, and drop any tables created by migrations
        # to prevent "psycopg2.errors.DuplicateTable" collisions [14]
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA IF NOT EXISTS "supply_chain_schema";')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."wallets" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."blockchain_transactions" CASCADE;')
            cursor.execute('DROP TABLE IF EXISTS "supply_chain_schema"."ownership_history" CASCADE;')
        
        # 2. Dynamically build the unmanaged database tables cleanly for testing
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Wallet)
            schema_editor.create_model(BlockchainTransaction)
            schema_editor.create_model(OwnershipHistory)
            
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            try:
                schema_editor.delete_model(Wallet)
                schema_editor.delete_model(BlockchainTransaction)
                schema_editor.delete_model(OwnershipHistory)
            except Exception:
                pass
        super().tearDownClass()

    def setUp(self):
        # Initialize native REST Framework APIClient to test template & API views cleanly [15]
        self.client = APIClient()
        self.admin_password = "secure_password_77"
        
        # Instantiate test user with the UUID primary key [2]
        self.admin_user = User.objects.create_superuser(
            email="admin@saaschain.com",
            password=self.admin_password,
            user_id=uuid.uuid4()
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

        # Seed global config record
        self.setting = SystemSetting = None  # Handled fallback in service layer

    def test_anonymous_is_redirected(self):
        """Verify anonymous requests are securely blocked."""
        response = self.client.get(reverse('blockchain:wallet-list'))
        self.assertEqual(response.status_code, 302)

    def test_auth_challenge_generates_nonce(self):
        """Verify challenge generation binds secure nonce to the session."""
        self.client.force_login(self.admin_user)          # Prepares standard session
        self.client.force_authenticate(user=self.admin_user)  # Prepares REST permissions [15]
        
        response = self.client.get(reverse('blockchain:api-wallet-challenge'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("challenge", response.json())
        self.assertTrue(response.json()["challenge"].startswith("Sign this cryptographic message"))

    def test_invalid_signature_is_rejected(self):
        """Verify mismatched cryptographic signature returns 401 unauthorized."""
        self.client.force_login(self.admin_user)          # Prepares standard session
        self.client.force_authenticate(user=self.admin_user)  # Prepares REST permissions [15]
        
        # Bind challenge to session first
        session = self.client.session
        session['wallet_auth_challenge'] = "Challenge nonce mockup"
        session.save()

        payload = {
            "wallet_address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
            "signature": "0xinvalid_sig_proof"
        }
        
        response = self.client.post(
            reverse('blockchain:api-wallet-verify'),
            data=payload,
            format='json'
        )
        self.assertEqual(response.status_code, 401)