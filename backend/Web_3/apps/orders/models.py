# apps/orders/models.py
import uuid
from django.db import models

class Order(models.Model):
    # Primary Key
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    buyer_company = models.ForeignKey(
        'companies.Company',  
        on_delete=models.PROTECT,
        db_column='buyer_company_id',
        related_name='buyer_orders'
    )
    
    seller_company = models.ForeignKey(
        'companies.Company',  
        on_delete=models.PROTECT,
        db_column='seller_company_id',
        related_name='seller_orders'
    )
    
    # Order Details
    order_number = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    order_status = models.CharField(max_length=50)
    
    # Dates & Timestamps
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."orders"'
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order {self.order_number} ({self.order_status})"


class OrderItem(models.Model):
    # Primary Key
    order_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='items'
    )
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        db_column='product_id',
        related_name='order_items'
    )
    
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."order_items"'
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"Item {self.product.product_name} x {self.quantity}"