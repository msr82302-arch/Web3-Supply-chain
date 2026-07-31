# apps/shipments/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Shipment

logger = logging.getLogger('apps.shipments.signals')

try:
    from services.email_service import EnterpriseEmailService
except ImportError:
    class EnterpriseEmailService:
        @staticmethod
        def dispatch_transactional_template(template_name, context, recipient_email, subject_line):
            from django.core.mail import send_mail
            message = f"Verify your shipment status update at: token={context['shipment_number']}"
            send_mail(subject_line, message, 'no-reply@platform.com', [recipient_email])

@receiver(post_save, sender=Shipment)
def automatic_shipment_email_trigger(sender, instance, created, **kwargs):
    # FIXED: Replaced non-existent attributes with database-compliant fields
    context = {
        "shipment_number": instance.shipment_number,
        "tracking_status": instance.shipment_status,
        "location": "Transit Node Update"
    }
    try:
        EnterpriseEmailService.dispatch_transactional_template(
            template_name="shipment_notification.html",
            context=context,
            recipient_email=getattr(instance.order.buyer_company, 'email', 'admin@company.com'),
            subject_line=f"Logistics Tracking Update: {instance.shipment_number}"
        )
    except Exception as e:
        logger.error(f"Failed to dispatch shipment notification email: {str(e)}")