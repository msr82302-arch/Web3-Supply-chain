# apps/orders/selectors.py
from django.db.models import Q
from apps.orders.models import Order

class OrderSelector:
    @staticmethod
    def get_visible_orders(user):
        """
        Enforces clear multi-tenant data boundaries:
        - System superusers/global staff can access all transaction records.
        - Regular users are limited strictly to orders they buyers or sellers participate in.
        """
        if not user or user.is_anonymous:
            return Order.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return Order.objects.all()

        user_company = getattr(user, 'company', None)
        if not user_company:
            return Order.objects.none()

        # FIXED: Extract raw UUID to bypass model class type checks completely
        company_uuid = user_company.company_id

        return Order.objects.filter(
            Q(buyer_company_id=company_uuid) | Q(seller_company_id=company_uuid)
        ).distinct()