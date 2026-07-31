import uuid
from django.db import models
from apps.products.models import Product

class Wallet(models.Model):
    wallet_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()  
    wallet_address = models.CharField(max_length=100)
    blockchain_network = models.CharField(max_length=50)
    wallet_provider = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."wallets"'


class BlockchainTransaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nft_id = models.UUIDField(blank=True, null=True)
    transaction_hash = models.CharField(max_length=255)
    block_number = models.BigIntegerField()
    network = models.CharField(max_length=50)
    gas_fee = models.DecimalField(max_digits=18, decimal_places=8)
    transaction_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50)  # PENDING, SUBMITTED, CONFIRMING, CONFIRMED, FAILED, REVERTED
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."blockchain_transactions"'


class OwnershipHistory(models.Model):
    ownership_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column='product_id',
        related_name='ownership_records'
    )
    previous_owner = models.UUIDField(blank=True, null=True)
    current_owner = models.UUIDField()
    blockchain_transaction = models.ForeignKey(
        BlockchainTransaction,
        on_delete=models.PROTECT,
        db_column='blockchain_transaction_id',
        related_name='ownership_transfers',
        blank=True,
        null=True
    )
    transfer_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."ownership_history"'