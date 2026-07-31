import uuid
from django.db import models

class SystemSetting(models.Model):
    id = models.BigAutoField(primary_key=True)
    application_name = models.CharField(max_length=150, default='Web3 Supply Chain SaaS')
    company_name = models.CharField(max_length=150, null=True, blank=True)
    company_email = models.CharField(max_length=150, null=True, blank=True)
    company_phone = models.CharField(max_length=30, null=True, blank=True)
    company_address = models.TextField(null=True, blank=True)
    company_logo = models.TextField(null=True, blank=True)
    company_website = models.CharField(max_length=255, null=True, blank=True)
    timezone = models.CharField(max_length=100, default='UTC')
    language = models.CharField(max_length=50, default='English')
    currency = models.CharField(max_length=20, default='USD')
    date_format = models.CharField(max_length=30, default='DD-MM-YYYY')
    theme = models.CharField(max_length=20, default='light')
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    email_verification = models.BooleanField(default=True)
    enable_notifications = models.BooleanField(default=True)
    enable_blockchain = models.BooleanField(default=True)
    blockchain_network = models.CharField(max_length=100, default='Ethereum')
    blockchain_rpc_url = models.TextField(null=True, blank=True)
    explorer_url = models.TextField(null=True, blank=True)
    nft_contract_address = models.CharField(max_length=255, null=True, blank=True)
    erc20_contract_address = models.CharField(max_length=255, null=True, blank=True)
    erc1155_contract_address = models.CharField(max_length=255, null=True, blank=True)
    
    # Decoupled UUID fields to bypass multi-app circular validation
    default_wallet = models.UUIDField(null=True, blank=True, db_column='default_wallet')
    
    smtp_host = models.CharField(max_length=255, null=True, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=255, null=True, blank=True)
    smtp_email = models.CharField(max_length=255, null=True, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    openai_enabled = models.BooleanField(default=False)
    ipfs_provider = models.CharField(max_length=100, null=True, blank=True)
    storage_provider = models.CharField(max_length=100, null=True, blank=True)
    
    created_by = models.UUIDField(null=True, blank=True, db_column='created_by')
    updated_by = models.UUIDField(null=True, blank=True, db_column='updated_by')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Schema mutations handled directly in PostgreSQL
        db_table = '"supply_chain_schema"."system_settings"'
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"