# apps/companies/models.py
import uuid
from django.db import models

class CompanyType(models.TextChoices):
    MANUFACTURER = 'MANUFACTURER', 'Manufacturer'
    SUPPLIER = 'SUPPLIER', 'Supplier'
    BUYER = 'BUYER', 'Buyer'
    DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor'
    LOGISTICS_PROVIDER = 'LOGISTICS_PROVIDER', 'Logistics Provider'
    RETAILER = 'RETAILER', 'Retailer'
    AUDITOR = 'AUDITOR', 'Auditor'
    ADMIN = 'ADMIN', 'Admin'

class CompanyStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Verification'
    VERIFIED = 'VERIFIED', 'Verified/Active'
    REVOKED = 'REVOKED', 'Revoked/Suspended'

class Company(models.Model):
    # Primary Key matching database screenshot exactly
    company_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Text Fields
    company_name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=100, blank=True, null=True, choices=CompanyType.choices)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_number = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    logo_url = models.TextField(blank=True, null=True)
    
    # Flags and Statuses matching database screenshot exactly
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default=CompanyStatus.PENDING, choices=CompanyStatus.choices, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."companies"'
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.company_name


class CompanyAddress(models.Model):
    address_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        db_column='company_id', 
        related_name='addresses'
    )
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    street_address = models.TextField()
    latitude = models.DecimalField(decimal_places=7, max_digits=10, blank=True, null=True)
    longitude = models.DecimalField(decimal_places=7, max_digits=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  
        db_table = '"supply_chain_schema"."company_addresses"'
        verbose_name = "Company Address"
        verbose_name_plural = "Company Addresses"