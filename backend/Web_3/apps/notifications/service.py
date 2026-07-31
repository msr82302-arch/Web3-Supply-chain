from django.db import transaction
from apps.notifications.models import Notification

class NotificationService:
    @staticmethod
    @transaction.atomic
    def dispatch_alert(alert_payload) -> Notification:
        """Securely inserts a system alert row into the unmanaged notifications table."""
        return Notification.objects.create(is_read=False, **alert_payload)

    @staticmethod
    @transaction.atomic
    def bulk_mark_as_read(user_id) -> int:
        """Executes a performance-optimized bulk update operation to clear unread counts."""
        updated_count = Notification.objects.filter(user_id=user_id, is_read=False).update(is_read=True)
        return updated_count
