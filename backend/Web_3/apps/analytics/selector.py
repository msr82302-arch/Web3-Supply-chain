# apps/analytics/selectors.py
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model
from apps.analytics.models import AIAnalysis, FraudReport, AuditLog
from apps.products.models import Product
from apps.orders.models import Order
from apps.shipments.models import Shipment
from apps.nft.models import NFT

User = get_user_model()

class AnalyticsSelector:
    @staticmethod
    def get_visible_analyses(user):
        """Enforces company-level tenant isolation on ML evaluations."""
        if not user or user.is_anonymous:
            return AIAnalysis.objects.none()
            
        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return AIAnalysis.objects.all().select_related('product')

        user_company = getattr(user, 'company', None)
        if not user_company:
            return AIAnalysis.objects.none()

        return AIAnalysis.objects.filter(
            product__manufacturer_company_id=user_company.company_id
        ).select_related('product')

    @staticmethod
    def get_visible_fraud_reports(user):
        """Enforces company-level tenant isolation on security risk reports."""
        if not user or user.is_anonymous:
            return FraudReport.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        if is_super:
            return FraudReport.objects.all().select_related('product', 'ai_analysis')

        user_company = getattr(user, 'company', None)
        if not user_company:
            return FraudReport.objects.none()

        return FraudReport.objects.filter(
            product__manufacturer_company_id=user_company.company_id
        ).select_related('product', 'ai_analysis')

    @staticmethod
    def get_visible_audit_logs(user):
        """Enforces strict role-based and company-level isolation on system governance audit logs."""
        if not user or user.is_anonymous:
            return AuditLog.objects.none()

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        role_name = getattr(user.role, 'role_name', '').upper() if user.role else ''
        
        if is_super or role_name in ['AUDITOR', 'ADMIN', 'ADMINISTRATOR']:
            return AuditLog.objects.all()

        user_company = getattr(user, 'company', None)
        if not user_company:
            return AuditLog.objects.none()

        # Retrieve all SCM ledger users belonging to this specific company partition space
        company_user_ids = User.objects.filter(company=user_company).values_list('user_id', flat=True)
        return AuditLog.objects.filter(user_id__in=company_user_ids)

    @staticmethod
    def get_company_ledger_metrics(user) -> dict:
        """
        Uses database-side Count aggregation patterns to compile company-level SCM metrics.
        Returns global metrics for platform admins, and tenant-scoped metrics for company operators.
        """
        if not user or user.is_anonymous:
            return {}

        is_super = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        user_company = getattr(user, 'company', None)

        if is_super:
            # Global analytics readout for platform administrators
            products_qs = Product.objects.all()
            orders_qs = Order.objects.all()
            shipments_qs = Shipment.objects.all()
        else:
            if not user_company:
                return {}
            # Scoped data arrays protecting competitor metrics
            products_qs = Product.objects.filter(manufacturer_company_id=user_company.company_id)
            orders_qs = Order.objects.filter(Q(buyer_company_id=user_company.company_id) | Q(seller_company_id=user_company.company_id))
            shipments_qs = Shipment.objects.filter(Q(order__buyer_company_id=user_company.company_id) | Q(order__seller_company_id=user_company.company_id))

        # Perform database-side Count aggregations to prevent memory leaks and N+1 queries
        return {
            'total_products': products_qs.count(),
            'active_products': products_qs.filter(current_status='ACTIVE').count(),
            'tokenized_products': products_qs.filter(current_status='TOKENIZED').count(),
            'total_orders': orders_qs.count(),
            'pending_orders': orders_qs.filter(order_status='PENDING').count(),
            'completed_orders': orders_qs.filter(order_status='COMPLETED').count(),
            'active_shipments': shipments_qs.exclude(shipment_status='DELIVERED').count(),
            'delivered_shipments': shipments_qs.filter(shipment_status='DELIVERED').count(),
        }