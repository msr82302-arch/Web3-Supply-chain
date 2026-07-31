# apps/companies/serializers.py
from rest_framework import serializers
from apps.companies.models import Company, CompanyAddress

class CompanyAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAddress
        fields = [
            'address_id', 'company', 'country', 'state', 'city', 
            'postal_code', 'street_address', 'latitude', 'longitude', 
            'created_at', 'updated_at'
        ]
        extra_kwargs = {'company': {'required': False, 'write_only': True}}


class CompanyDetailSerializer(serializers.ModelSerializer):
    addresses = CompanyAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = [
            'company_id', 'company_name', 'company_type', 'registration_number', 
            'tax_number', 'email', 'phone', 'website', 'logo_url', 
            'is_verified', 'status', 'created_at', 'updated_at', 'addresses'
        ]
        read_only_fields = fields


class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    addresses = CompanyAddressSerializer(many=True, required=False)

    class Meta:
        model = Company
        fields = [
            'company_id', 'company_name', 'company_type', 'registration_number', 
            'tax_number', 'email', 'phone', 'website', 'logo_url', 
            'is_verified', 'status', 'created_at', 'updated_at', 'addresses'
        ]
        read_only_fields = ['company_id', 'is_verified', 'status', 'created_at', 'updated_at']

    def validate_registration_number(self, value):
        if not value: return value
        norm = str(value).strip().upper()
        inst_id = getattr(self.instance, 'company_id', None)
        qs = Company.objects.filter(registration_number__iexact=norm)
        if inst_id: qs = qs.exclude(company_id=inst_id)
        if qs.exists():
            raise serializers.ValidationError("An enterprise with this registration number is already registered.")
        return norm

    def validate_tax_number(self, value):
        if not value: return value
        norm = str(value).strip().upper()
        inst_id = getattr(self.instance, 'company_id', None)
        qs = Company.objects.filter(tax_number__iexact=norm)
        if inst_id: qs = qs.exclude(company_id=inst_id)
        if qs.exists():
            raise serializers.ValidationError("Ecosystem Registry Refusal: This specific tax number identifier node already exists.")
        return norm