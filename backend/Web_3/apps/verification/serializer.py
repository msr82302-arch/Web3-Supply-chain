# apps/verification/serializers.py
from rest_framework import serializers
from apps.verification.models import QRCode, VerificationLog

class VerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationLog
        fields = [
            'verification_log_id', 'qr', 'verified_by', 'ip_address', 
            'device_info', 'country', 'city', 'latitude', 'longitude', 
            'verification_result', 'verified_at'
        ]
        extra_kwargs = {
            'ip_address': {'required': False, 'allow_null': True},
            'device_info': {'required': False, 'allow_null': True}
        }


class QRCodeDetailSerializer(serializers.ModelSerializer):
    """Provides a structural readout of a QR code asset along with its full scan audit logs."""
    verification_logs = VerificationLogSerializer(many=True, read_only=True)
    product_name = serializers.ReadOnlyField(source='product.product_name')

    class Meta:
        model = QRCode
        fields = ['qr_id', 'product', 'product_name', 'qr_code', 'qr_image_url', 'verification_url', 'is_active', 'generated_at', 'verification_logs']


class QRCodeCreateSerializer(serializers.ModelSerializer):
    """Validates data entry parameters when manufacturing fresh scannable labels."""
    class Meta:
        model = QRCode
        fields = ['qr_id', 'product', 'qr_code', 'qr_image_url', 'verification_url', 'is_active']