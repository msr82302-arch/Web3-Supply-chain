from django.db import models

# Create your models here.
import uuid


# Direct Python import to manage cross-app product relationships safely
from apps.products.models import Product

class QRCode(models.Model):
    # Primary Key
    qr_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Key mapping directly back to the physical tracked product
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column='product_id',
        related_name='qr_codes'
    )
    
    # QR Code Text and Assets
    qr_code = models.TextField()
    qr_image_url = models.TextField()
    verification_url = models.TextField()
    
    # Status Flags and Timestamps
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."qr_codes"'
        verbose_name = "QR Code"
        verbose_name_plural = "QR Codes"


class VerificationLog(models.Model):
    # Primary Key
    verification_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Key mapping back to the scanned QR code identity record
    qr = models.ForeignKey(
        QRCode,
        on_delete=models.PROTECT,
        db_column='qr_id',
        related_name='verification_logs'
    )
    
    # Loose UUID reference tracking authenticated users (nullable if public scans are allowed)
    verified_by = models.UUIDField(blank=True, null=True)
    
    # Metadata Captured From Scanner Client
    ip_address = models.CharField(max_length=100, blank=True, null=True)
    device_info = models.TextField(blank=True, null=True)
    
    # Location Metadata (Extracted via IP geolocation or client hardware)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # High-Precision Spatial Location (matching exactly numeric(10,7))
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    
    # Evaluation Outcome (e.g., 'SUCCESS', 'FRAUD_SUSPECTED', 'EXPIRED')
    verification_result = models.CharField(max_length=100)
    
    # Verification Event Timestamp
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."verification_logs"'
        verbose_name = "Verification Log"
        verbose_name_plural = "Verification Logs"
