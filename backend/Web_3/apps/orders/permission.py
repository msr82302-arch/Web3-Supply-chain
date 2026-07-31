# apps/orders/permissions.py
from rest_framework import permissions

class IsOrderParticipant(permissions.BasePermission):
    """
    Enforces strict company-level isolation:
    - Admins bypass blocks.
    - Regular users must belong to either the buyer or seller company of the target order.
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

        # FIXED: Enforce UUID-level matching to prevent class validation mismatches
        company_uuid = user_company.company_id
        return obj.buyer_company_id == company_uuid or obj.seller_company_id == company_uuid