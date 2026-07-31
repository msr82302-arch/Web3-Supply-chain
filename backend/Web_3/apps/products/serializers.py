import uuid
from rest_framework import serializers
from apps.products.models import (
    Product, 
    ProductCategory, 
    ProductImage, 
    ProductDocument, 
    ProductCertificate, 
    ProductStatusHistory
)
from apps.companies.models import Company, CompanyAddress

# =====================================================================
# 1. FOUNDATIONAL USER INTERFACE LAYERS (COMPANIES & CATEGORIES)
# =====================================================================

class CompanyAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAddress
        fields = [
            'address_id', 'country', 'state', 'city', 'postal_code', 
            'street_address', 'latitude', 'longitude', 'created_at'
        ]


class CompanySerializer(serializers.ModelSerializer):
    # Provides nested physical location profiles on frontend dashboard panes
    addresses = CompanyAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = [
            'company_id', 'company_name', 'company_type', 'registration_number',
            'tax_number', 'email', 'phone', 'website', 'logo_url', 
            'is_verified', 'status', 'created_at', 'updated_at', 'addresses'
        ]


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['category_id', 'category_name', 'description', 'created_at', 'updated_at']


# =====================================================================
# 2. FILE AND LOG ATTACHMENT ASSET EXTRACTIONS
# =====================================================================

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image_id', 'image_url', 'image_type', 'uploaded_at']


class ProductDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDocument
        fields = ['document_id', 'document_name', 'document_type', 'document_url', 'uploaded_by', 'uploaded_at']


class ProductCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCertificate
        fields = [
            'certificate_id', 'certificate_number', 'issuing_authority', 
            'issue_date', 'expiry_date', 'certificate_url', 'created_at'
        ]


class ProductStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStatusHistory
        fields = ['history_id', 'changed_by', 'old_status', 'new_status', 'remarks', 'changed_at']


# =====================================================================
# 3. CORE PRODUCT CORE TRANSFORMATION PIPELINES
# =====================================================================

class ProductDetailSerializer(serializers.ModelSerializer):
    """Provides deep-nested analytical tree readouts for frontend tracking interfaces."""
    category = ProductCategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    documents = ProductDocumentSerializer(many=True, read_only=True)
    certificates = ProductCertificateSerializer(many=True, read_only=True)
    status_history = ProductStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Handles mutation requests, validating unmanaged dataset structural invariants."""
    class Meta:
        model = Product
        fields = [
            'product_id', 'manufacturer_company_id', 'category', 'product_name', 
            'sku', 'serial_number', 'batch_number', 'manufacture_date', 
            'expiry_date', 'description', 'current_status', 'qr_code'
        ]

    def validate_manufacturer_company_id(self, value):
        """Cross-app referential lookup ensuring the manufacturer company exists in PostgreSQL."""
        if not Company.objects.filter(company_id=value).exists():
            raise serializers.ValidationError("The provided manufacturer company ID does not exist.")
        return value

    def validate(self, data):
        """Business rule validation checking time lifecycle coherence."""
        m_date = data.get('manufacture_date')
        e_date = data.get('expiry_date')
        if m_date and e_date and e_date < m_date:
            raise serializers.ValidationError({"expiry_date": "Expiry date cannot be prior to the manufacture date."})
        return data
