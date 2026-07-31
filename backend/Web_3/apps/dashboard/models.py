

# Create your models here.
# apps/shipments/models.py
from django.db import models
import uuid

class Shipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(max_length=50, unique=True)
    cargo_title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    telemetry_temp = models.DecimalField(max_digits=5, decimal_places=2, default=4.20)
    is_critical = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='active') # active, archived
    created_at = models.DateTimeField(auto_now_add=True)


# apps/products/models.py
from django.db import models

class Product(models.Model):
    sku = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='active') # active, pending
    escrow_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
