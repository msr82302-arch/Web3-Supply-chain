# apps/shipments/selectors.py
from django.db.models import Q
from apps.shipments.models import Shipment

class ShipmentSelector:
    @staticmethod
    def get_visible_shipments(user):
        """
        Enforces strict company-level tenant isolation:
        - Staff/Superusers can inspect all shipments.
        - Regular users can only see shipments where their company is the buyer, seller, or carrier.
        """
        if not user or user.is_anonymous:
            return Shipment.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return Shipment.objects.all()

        user_company = getattr(user, 'company', None)
        if not user_company:
            return Shipment.objects.none()

        company_uuid = user_company.company_id

        return Shipment.objects.filter(
            Q(order__buyer_company_id=company_uuid) |
            Q(order__seller_company_id=company_uuid) |
            Q(logistics_company_id=company_uuid)
        ).distinct()