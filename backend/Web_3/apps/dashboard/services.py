import logging
from apps.dashboard.selectors import DashboardSelector

logger = logging.getLogger(__name__)

# Resilient try-except block to handle custom auth serializers gracefully
try:
    from apps.accounts.serializers import UserDetailSerializer
except ImportError:
    UserDetailSerializer = None

class DashboardBusinessService:
    
    @staticmethod
    def compile_control_center_matrices(request) -> dict:
        """
        Orchestrates live telemetry calculations and injects user profile metadata
        straight from the authenticated request session context mapping.
        """
        user = request.user
        role_name = getattr(user.role, 'role_name', None) if hasattr(user, 'role') else None
        
        # Safe check of attributes that may be missing on custom User models [18]
        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False) or role_name in ['ADMIN', 'ADMINISTRATOR', 'Platform Administrator']
        company_id = None if is_platform_admin else getattr(user, 'company_id', None)

        # Extract statistics through our safe, isolated selectors
        products_count = DashboardSelector.count_products(company_id=company_id)
        shipments_count = DashboardSelector.count_shipments(company_id=company_id)
        escrow_value = DashboardSelector.get_escrow_total_value(company_id=company_id)
        block_height = DashboardSelector.get_blockchain_block_height()
        
        # Pull lists
        recent_shipments = DashboardSelector.get_recent_shipments(company_id=company_id, limit=5)
        recent_products = DashboardSelector.get_unverified_products(company_id=company_id, limit=5)

        # Serialize current operator information safely
        operator_data = None
        if user.is_authenticated:
            if UserDetailSerializer:
                try:
                    operator_data = UserDetailSerializer(user).data
                except Exception:
                    pass
            
            # Defensive fallback if Serializers fail or are missing
            if not operator_data:
                operator_data = {
                    "user_id": str(getattr(user, 'user_id', user.id)),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role_name": role_name or "Operational Operator"
                }

        # Assemble and return context dictionary
        return {
            "current_operator": operator_data,
            "escrow_total_value": f"${escrow_value:,.2f} USD" if escrow_value else "$0.00 USD",
            "shipments_count": f"{shipments_count} Batches" if shipments_count else "0 Batches",
            "products_count": f"{products_count} SKU" if products_count else "0 SKU",
            "block_height": block_height,
            "recent_shipments": recent_shipments,
            "recent_products": recent_products,
            "live_notifications_list": []  # Ready for real-time notification streams integration
        }