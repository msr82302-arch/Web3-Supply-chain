from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EnterpriseEmailService:
    @staticmethod
    def dispatch_transactional_template(template_name, context, recipient_email, subject_line):
        """
        Compiles and transmits multi-part HTML/text email structures 
        using the centralized base email framework layouts securely.
        """
        try:
            # 1. Dynamically render the DTL HTML layout from your global templates repository
            html_payload = render_to_string(f"emails/{template_name}", context)
            
            # 2. Extract a clean plain text fallback for legacy text terminals
            plain_text_payload = strip_tags(html_payload)
            
            # 3. Formulate the explicit multi-part mail object layer
            message = EmailMultiAlternatives(
                subject=subject_line,
                body=plain_text_payload,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            message.attach_alternative(html_payload, "text/html")
            
            # 4. Trigger synchronous network transmission across SMTP configurations
            message.send(fail_silently=False)
            logger.info(f"[EMAIL_SUCCESS] Dispatched '{template_name}' to {recipient_email}")
            return True
            
        except Exception as error:
            logger.error(f"[EMAIL_FAILURE] Failed dispatching '{template_name}' to {recipient_email}. Context: {str(error)}")
            return False
