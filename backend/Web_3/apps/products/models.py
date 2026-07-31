from django.db import models

# Create your models here.
import uuid


class ProductCategory(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."product_categories"'
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"


class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key pointing back to companies app/table (assumed structure from context)
    manufacturer_company_id = models.UUIDField() 
    
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        db_column='category_id',
        related_name='products'
    )
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    current_status = models.CharField(max_length=50)
    qr_code = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."products"'
        verbose_name = "Product"
        verbose_name_plural = "Products"


class ProductImage(models.Model):
    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='images'
    )
    image_url = models.TextField()
    image_type = models.CharField(max_length=50, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."product_images"'


class ProductDocument(models.Model):
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='documents'
    )
    document_name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100)
    document_url = models.TextField()
    uploaded_by = models.UUIDField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."product_documents"'


class ProductCertificate(models.Model):
    certificate_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='certificates'
    )
    certificate_number = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    certificate_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."product_certificates"'


class ProductStatusHistory(models.Model):
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='status_history'
    )
    changed_by = models.UUIDField()
    old_status = models.CharField(max_length=50, blank=True, null=True)
    new_status = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."product_status_history"'
        verbose_name_plural = "Product status histories"
