# apps/verification/permissions.py
from rest_framework import permissions
from apps.verification.selector import VerificationSelector

class IsVerificationParticipant(permissions.BasePermission):
    """
    Enforces strict company-level tenant boundaries:
    - Admins bypass blocks.
    - Regular users must belong to the manufacturer company of the product associated with the QR code.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if is_super:
            return True

        user_company = getattr(request.user, 'company', None)
        if not user_company:
            return False

        return obj.product.manufacturer_company_id == user_company.company_id