# apps/orders/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

logger = logging.getLogger('apps.orders.signals')

try:
    from services.email_service import EnterpriseEmailService
except ImportError:
    class EnterpriseEmailService:
        @staticmethod
        def dispatch_transactional_template(template_name, context, recipient_email, subject_line):
            from django.core.mail import send_mail
            message = f"Settled Invoice Link: token={context['order_number']}"
            send_mail(subject_line, message, 'no-reply@platform.com', [recipient_email])

@receiver(post_save, sender=Order)
def trigger_invoice_ledger_dispatch(sender, instance, created, **kwargs):
    # FIXED: Corrected attribute lookup to prevent unhandled AttributeError crash
    if instance.order_status == "PAID":
        context = {
            "order_id": instance.order_id,
            "order_number": instance.order_number,
            "gross_total": instance.total_amount,
            "items_list": instance.items.all()
        }
        try:
            EnterpriseEmailService.dispatch_transactional_template(
                template_name="invoice.html",
                context=context,
                recipient_email=getattr(instance.buyer_company, 'email', 'admin@company.com'),
                subject_line=f"Invoice Settlement Receipt: {instance.order_number}"
            )
        except Exception as e:
            logger.error(f"Failed to dispatch transaction email: {str(e)}")