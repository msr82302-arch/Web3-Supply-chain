# apps/notifications/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Notification

logger = logging.getLogger('apps.notifications.signals')
User = get_user_model()

try:
    from services.email_service import EnterpriseEmailService
except ImportError:
    class EnterpriseEmailService:
        @staticmethod
        def dispatch_transactional_template(template_name, context, recipient_email, subject_line):
            from django.core.mail import send_mail
            message = f"Alert dispatch: {context['location']}"
            send_mail(subject_line, message, 'no-reply@platform.com', [recipient_email])

@receiver(post_save, sender=Notification)
def trigger_global_broadcast_notifications(sender, instance, created, **kwargs):
    """
    Monitors fallback global alerts and custom system communications.
    """
    if created:  
        # FIXED: Resolved user lookup to safely retrieve corporate notification email
        try:
            target_user = User.objects.get(user_id=instance.user_id)
            recipient_email = target_user.email
        except User.DoesNotExist:
            recipient_email = "admin@company.com"

        # FIXED: Corrected attribute lookup mapping to verified database fields
        context = {
            "shipment_number": str(instance.notification_id)[:8].upper(),
            "tracking_status": instance.notification_type,
            "location": instance.message,
            "recorded_at": instance.created_at
        }
        try:
            EnterpriseEmailService.dispatch_transactional_template(
                template_name="emails/shipment_notification.html",
                context=context,
                recipient_email=recipient_email,
                subject_line=f"System Alert Core Monitor: {instance.title}"
            )
        except Exception as e:
            logger.error(f"Failed to dispatch alert notification email: {str(e)}")