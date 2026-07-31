from rest_framework import serializers
from apps.shipments.models import Shipment, ShipmentTracking

class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = ['tracking_id', 'shipment', 'latitude', 'longitude', 'location', 'tracking_status', 'recorded_at']
        extra_kwargs = {'shipment': {'required': False}}


class ShipmentDetailSerializer(serializers.ModelSerializer):
    """Provides complete shipping manifests containing nested real-time telemetry events."""
    tracking_events = ShipmentTrackingSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = '__all__'


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Validates parameters for shipping manifests form submittals."""
    class Meta:
        model = Shipment
        fields = ['shipment_id', 'order', 'logistics_company', 'shipment_number', 'tracking_number', 'shipment_status', 'expected_arrival']
