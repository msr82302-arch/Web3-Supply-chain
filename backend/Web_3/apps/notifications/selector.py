# apps/notifications/selectors.py
from apps.notifications.models import Notification

class NotificationSelector:
    @staticmethod
    def get_user_notifications(user):
        """
        Enforces strict multi-tenant and user-level boundaries:
        - Regular users can only access notifications addressed directly to their user_id.
        """
        if not user or user.is_anonymous:
            return Notification.objects.none()
            
        return Notification.objects.filter(user_id=user.user_id).order_by('-created_at')