# apps/nft/services.py
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.nft.models import NFT
from apps.blockchain.models import OwnershipHistory
from apps.products.services import ProductService

class NFTService:
    @staticmethod
    @transaction.atomic
    def record_minted_twin(nft_payload) -> NFT:
        """Securely logs a digital twin certificate and transitions product state to TOKENIZED."""
        product = nft_payload.get('product')
        if not product:
            raise ValidationError("A valid product is required to mint a digital twin.")

        # Duplicate minting guard
        if NFT.objects.filter(product=product).exists():
            raise ValidationError("A digital twin NFT has already been minted for this product.")

        nft = NFT.objects.create(
            minted_at=timezone.now(),
            **nft_payload
        )

        # Transition product state to TOKENIZED atomically
        ProductService.update_product_status(
            product=product,
            new_status="TOKENIZED",
            acting_user_id=nft_payload['minted_by'],
            remarks=f"Ecosystem ledger: NFT twin generated. Token ID: {nft.token_id}."
        )

        return nft

    @staticmethod
    @transaction.atomic
    def record_ownership_transfer(transfer_payload) -> OwnershipHistory:
        """Atomically locks an asset custody transfer entry into PostgreSQL."""
        return OwnershipHistory.objects.create(
            transfer_date=timezone.now(),
            **transfer_payload
        )