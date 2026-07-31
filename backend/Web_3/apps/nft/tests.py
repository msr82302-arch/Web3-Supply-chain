# apps/nft/tests.py
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from eth_account import Account
from eth_account.messages import encode_defunct

from apps.companies.models import Company, CompanyType
from apps.products.models import Product, ProductCategory
from apps.nft.models import NFT
from apps.nft.service import NFTService

# Set managed=True at the module-level so that unmanaged tables 
# are correctly generated in the test database during initialization.
NFT._meta.managed = True
Product._meta.managed = True
ProductCategory._meta.managed = True
Company._meta.managed = True

User = get_user_model()

@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
    'products': None,
    'nft': None,
})
class NFTStabilizationTests(TestCase):
    def setUp(self):
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

        self.creator_user.company_id = self.company_a.company_id
        self.creator_user.save()

        self.category = ProductCategory.objects.create(
            category_name="Plastics",
            description="Industrial raw plastics"
        )

        self.product = Product.objects.create(
            manufacturer_company_id=self.company_a.company_id,
            category=self.category,
            product_name="Product Alpha",
            sku="SKU-A1",
            batch_number="BATCH-A1",
            current_status="MANUFACTURED"
        )

        self.client = Client()

    def test_minting_fails_on_duplicate_product_registration(self):
        # 1. First mint succeeds
        NFTService.record_minted_twin({
            'product': self.product,
            'token_id': 101,
            'contract_address': "0x1111222233334444555566667777888899990000",
            'ipfs_hash': "QmX123",
            'metadata_uri': "ipfs://QmX123",
            'minted_by': self.creator_user.user_id
        })

        # 2. Second mint request for the identical product must raise ValidationError
        with self.assertRaises(ValidationError):
            NFTService.record_minted_twin({
                'product': self.product,
                'token_id': 102,
                'contract_address': "0x1111222233334444555566667777888899990000",
                'ipfs_hash': "QmX456",
                'metadata_uri': "ipfs://QmX456",
                'minted_by': self.creator_user.user_id
            })

    def test_cryptographic_signature_challenge_response(self):
        # 1. Fetch challenge nonce from viewset
        # FIXED: Changed namespace mapping from accounts:nft to nft
        response_chal = self.client.get(reverse('nft:wallet_challenge_api'))
        self.assertEqual(response_chal.status_code, 200)
        chal_data = response_chal.json()
        
        # 2. Generate a valid mock private key and sign the challenge string
        wallet_key = Account.create()
        message = encode_defunct(text=chal_data['challenge'])
        signature = Account.sign_message(message, private_key=wallet_key.key).signature.hex()

        # 3. Post verification request to views layer
        # FIXED: Changed namespace mapping from accounts:nft to nft
        response_verify = self.client.post(reverse('nft:wallet_verify_api'), {
            'wallet_address': wallet_key.address,
            'signature': signature
        })
        self.assertEqual(response_verify.status_code, 200)
        self.assertTrue(response_verify.json()['success'])