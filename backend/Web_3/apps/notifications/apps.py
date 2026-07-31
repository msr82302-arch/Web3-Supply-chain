from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        """
        Initializes fallback global alerts and custom system communication streams on runtime boot.
        Handles: Generic system broadcast communications.
        """
        import apps.notifications.signals
