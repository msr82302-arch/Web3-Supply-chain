# apps/shipments/permissions.py
from rest_framework import permissions

class IsShipmentParticipant(permissions.BasePermission):
    """
    Enforces strict company-level tenant boundaries:
    - Admins bypass blocks.
    - Regular users must belong to either the buyer, seller, or carrier of the shipment.
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

        company_uuid = user_company.company_id
        return (
            obj.order.buyer_company_id == company_uuid or
            obj.order.seller_company_id == company_uuid or
            obj.logistics_company_id == company_uuid
        )