# apps/verification/selectors.py
from apps.verification.models import QRCode, VerificationLog

class VerificationSelector:
    @staticmethod
    def get_visible_qr_codes(user):
        """
        Enforces clear multi-tenant boundaries:
        - System superusers/global staff can access all QR codes.
        - Regular users can only access QR codes linked to products manufactured by their company.
        """
        if not user or user.is_anonymous:
            return QRCode.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return QRCode.objects.all().select_related('product')

        user_company = getattr(user, 'company', None)
        if not user_company:
            return QRCode.objects.none()

        return QRCode.objects.filter(product__manufacturer_company_id=user_company.company_id).select_related('product')

    @staticmethod
    def get_visible_verification_logs(user):
        """Enforces company-level tenant isolation on verification logs."""
        if not user or user.is_anonymous:
            return VerificationLog.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return VerificationLog.objects.all().select_related('qr__product')

        user_company = getattr(user, 'company', None)
        if not user_company:
            return VerificationLog.objects.none()

        return VerificationLog.objects.filter(qr__product__manufacturer_company_id=user_company.company_id).select_related('qr__product')