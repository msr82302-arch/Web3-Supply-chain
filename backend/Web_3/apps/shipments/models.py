from django.db import models

# Create your models here.
import uuid

# Direct Python imports to guarantee smooth cross-app relationships
from apps.orders.models import Order
from apps.companies.models import Company

class Shipment(models.Model):
    # Primary Key
    shipment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Key pointing to Orders app
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        db_column='order_id',
        related_name='shipments'
    )
    
    # Foreign Key pointing back to Companies app (Logistics Entity)
    logistics_company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        db_column='logistics_company_id',
        related_name='logistics_shipments'
    )
    
    # Tracking and Identification Data
    shipment_number = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipment_status = models.CharField(max_length=50)
    
    # Timeline Stamps
    departure_date = models.DateTimeField(blank=True, null=True)
    expected_arrival = models.DateField(blank=True, null=True)
    actual_arrival = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."shipments"'
        verbose_name = "Shipment"
        verbose_name_plural = "Shipments"


class ShipmentTracking(models.Model):
    # Primary Key
    tracking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Key to parent Shipment
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        db_column='shipment_id',
        related_name='tracking_events'
    )
    
    # Geospatial Routing Telemetry
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Status and Location text
    location = models.CharField(max_length=255)
    tracking_status = models.CharField(max_length=100)
    
    # Event Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."shipment_tracking"'
        verbose_name = "Shipment Tracking"
        verbose_name_plural = "Shipment Tracking Logs"
