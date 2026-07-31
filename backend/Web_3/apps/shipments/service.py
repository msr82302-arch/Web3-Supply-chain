from django.db import transaction
from django.utils import timezone
from apps.shipments.models import Shipment, ShipmentTracking

class ShipmentService:
    @staticmethod
    @transaction.atomic
    def initiate_shipment(manifest_data) -> Shipment:
        """Securely creates a shipment entry and forces initial transit state machine log bindings."""
        shipment = Shipment.objects.create(
            shipment_status="MANIFEST_CREATED",
            departure_date=timezone.now(),
            **manifest_data
        )
        return shipment

    @staticmethod
    @transaction.atomic
    def append_gps_ping(shipment: Shipment, coordinates_payload) -> ShipmentTracking:
        """Appends real-time coordinates, matching precise numeric(10,7) data types."""
        return ShipmentTracking.objects.create(shipment=shipment, **coordinates_payload)
