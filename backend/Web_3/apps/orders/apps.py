from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'

    def ready(self):
        """
        Initializes financial transaction ledger and transactional billing triggers on runtime boot.
        Handles: Purchase Order, Invoice Settlement receipts.
        """
        import apps.orders.signals
