# apps/nft/models.py
import uuid
from django.db import models
from apps.products.models import Product

class NFT(models.Model):
    nft_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column='product_id',
        related_name='nfts'
    )
    token_id = models.BigIntegerField()
    contract_address = models.CharField(max_length=255)
    ipfs_hash = models.TextField()
    metadata_uri = models.TextField()
    minted_by = models.UUIDField()
    minted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."nfts"'
        verbose_name = "NFT"
        verbose_name_plural = "NFTs"

    def __str__(self):
        return f"NFT Token {self.token_id} for Product {self.product.product_id}"


class Wallet(models.Model):
    wallet_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    wallet_address = models.CharField(max_length=42, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."wallets"'

    def __str__(self):
        return self.wallet_address