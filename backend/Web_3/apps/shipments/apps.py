from django.apps import AppConfig

class ShipmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shipments'

    def ready(self):
        """
        Initializes real-time logistics telemetry notification triggers on runtime boot.
        Handles: Shipment Created, Delivered, Delayed triggers.
        """
        import apps.shipments.signals
