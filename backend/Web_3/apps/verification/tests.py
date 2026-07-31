# apps/verification/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
import time

from apps.companies.models import Company, CompanyType
from apps.products.models import Product, ProductCategory
from apps.verification.models import QRCode, VerificationLog
from apps.verification.service import VerificationService
from apps.accounts.models import Role # Imported Role

# Set managed=True for tests
QRCode._meta.managed = True
VerificationLog._meta.managed = True
Product._meta.managed = True
ProductCategory._meta.managed = True
Company._meta.managed = True
Role._meta.managed = True

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
    'verification': None,
})
class VerificationStabilizationTests(TestCase):
    def setUp(self):
        # FIXED: Provision non-nullable Role instances before user creations
        self.manufacturer_role = Role.objects.create(role_name="MANUFACTURER", description="Manufacturer Operator")

        self.operator_user = User.objects.create_user(
            email="operator@scm.com",
            password="securepassword123",
            first_name="SCM",
            last_name="Operator",
            role=self.manufacturer_role # FIXED: Passed role instance
        )

        self.company = Company.objects.create(
            company_name="Acme SCM Corp",
            company_type=CompanyType.MANUFACTURER,
            registration_number="REG-V1",
            tax_number="TAX-V1",
            is_verified=True
        )

        self.operator_user.company_id = self.company.company_id
        self.operator_user.save()

        self.category = ProductCategory.objects.create(
            category_name="Medical",
            description="SCM Medical items"
        )

        self.product = Product.objects.create(
            manufacturer_company_id=self.company.company_id,
            category=self.category,
            product_name="SCM Product Alpha",
            sku="SKU-V1",
            batch_number="BATCH-V1",
            current_status="MANUFACTURED"
        )

        self.client = Client()

    def test_cryptographic_verification_flow(self):
        qr = VerificationService.issue_qr_label({
            'product': self.product,
            'qr_code': "SCM_LABEL_001",
            'qr_image_url': "http://platform.com/qr/001.png",
            'verification_url': f"http://127.0.0.1:8000/verification/verify/"
        })

        timestamp = int(time.time())
        sig = VerificationService.generate_dynamic_signature(str(qr.qr_id), timestamp)

        url = reverse('verification:public_verify', kwargs={'qr_id': qr.qr_id})
        response = self.client.get(f"{url}?ts={timestamp}&sig={sig}")
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_authentic'])

    def test_invalid_signature_rejection_marks_fraud(self):
        qr = VerificationService.issue_qr_label({
            'product': self.product,
            'qr_code': "SCM_LABEL_001",
            'qr_image_url': "http://platform.com/qr/001.png",
            'verification_url': f"http://127.0.0.1:8000/verification/verify/"
        })

        url = reverse('verification:public_verify', kwargs={'qr_id': qr.qr_id})
        response = self.client.get(f"{url}?ts={int(time.time())}&sig=INVALID_SIGNATURE")
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_authentic'])
        self.assertEqual(response.context['log_entry'].verification_result, 'FRAUD_SUSPECTED')