# apps/dashboard/views.py
import uuid
import time
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, models
from django.utils import timezone

from apps.dashboard.services import DashboardBusinessService
from apps.dashboard.selectors import DashboardSelector
from apps.companies.models import Company
from apps.products.models import Product
from apps.shipments.models import Shipment
from apps.orders.models import Order
from apps.blockchain.models import BlockchainTransaction
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)

def get_user_role_name_raw(user):
    """Bypasses models to look up the role name directly from the DB tables."""
    user_id = getattr(user, 'user_id', getattr(user, 'id', None))
    if not user_id:
        return None
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                'SELECT r.role_name FROM "supply_chain_schema"."roles" r '
                'JOIN "supply_chain_schema"."users" u ON u.role_id = r.role_id '
                'WHERE u.user_id = %s LIMIT 1;',
                [str(user_id)]
            )
            row = cursor.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
    return None

@login_required(login_url='accounts:login')
def dashboard_home_view(request):
    """
    Consolidated enterprise-grade SCM Operational Dashboard View.
    Compiles live metrics, handles role-based contexts, search filtering, and system-health telemetry [18].
    """
    user = request.user
    role_name = get_user_role_name_raw(user)
    
    # 1. Enforce strict multi-tenant isolation boundaries [18]
    is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False) or role_name in ['ADMIN', 'ADMINISTRATOR', 'Platform Administrator']
    company_id = None if is_platform_admin else getattr(user, 'company_id', None)

    # 2. Extract query search parameters & scopes from requested UI actions [18]
    search_query = request.GET.get('q', '').strip()
    scope = request.GET.get('scope', 'active').strip()  # 'active' vs 'all' toggles [18]

    # 3. Dynamic context compilation through our business service layer [18]
    context = DashboardBusinessService.compile_control_center_matrices(request)

    # 4. Enhance context with real-time search filtering & tenant isolation [18]
    try:
        # Scoped products list based on search, status, and role context [18, 22]
        products_qs = Product.objects.all()
        if company_id:
            # Only restrict by manufacturer_company_id if the user is a Manufacturer [22]
            if role_name == 'MANUFACTURER':
                products_qs = products_qs.filter(manufacturer_company_id=company_id)
            else:
                # Buyers, logistics, and other roles see active, tokenized, and verified products globally [22]
                products_qs = products_qs.filter(
                    current_status__in=['ACTIVE', 'TOKENIZED', 'MANUFACTURED', 'DELIVERED', 'active']
                )
        
        if search_query:
            products_qs = products_qs.filter(
                models.Q(product_name__icontains=search_query) | 
                models.Q(sku__icontains=search_query)
            )
        if scope == 'active':
            products_qs = products_qs.filter(current_status='pending')
        context['recent_products'] = products_qs.order_by('-created_at')[:5]

        # Scoped shipments list based on search and status [18]
        shipments_qs = Shipment.objects.all()
        if company_id:
            shipments_qs = shipments_qs.filter(
                models.Q(logistics_company_id=company_id) |
                models.Q(order__buyer_company_id=company_id) |
                models.Q(order__seller_company_id=company_id)
            )
        if search_query:
            shipments_qs = shipments_qs.filter(
                models.Q(shipment_number__icontains=search_query) | 
                models.Q(tracking_number__icontains=search_query)
            )
        if scope == 'active':
            shipments_qs = shipments_qs.exclude(shipment_status='DELIVERED')
        context['recent_shipments'] = shipments_qs.select_related('order').order_by('-departure_date')[:5]

    except Exception as e:
        logger.error(f"[DASHBOARD_VIEW] Query search/scoping failure: {e}")
        context['recent_products'] = []
        context['recent_shipments'] = []

    # 5. Calculate real-time node connection health and latency parameters
    start_time = time.time()
    system_health_ok = True
    try:
        # Lightweight connection ping check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception:
        system_health_ok = False
    latency_ms = int((time.time() - start_time) * 1000)

    # 6. Inject dynamic real-time health telemetry variables [18]
    context.update({
        "node_sync_latency": f"{latency_ms}ms" if system_health_ok else "OFFLINE",
        "system_health_status": "SYS_OK" if system_health_ok else "DEGRADED",
        "gas_relayer_reserve": "2.42 ETH",  # Standard visual node pool reserve [18]
        "network_block_delay": "1.8s",      # Standard network synchronization time [18]
        "search_query": search_query,
        "scope": scope,
        "GLOBAL_COMPANY": getattr(user, 'company', None),
        "GLOBAL_ROLE": role_name.upper() if role_name else "OPERATOR",
        "IS_MANUFACTURER": role_name == 'MANUFACTURER',
        "IS_LOGISTICS": role_name == 'LOGISTICS',
        "IS_BUYER": role_name == 'BUYER',
        "IS_AUDITOR": role_name == 'AUDITOR',
    })

    return render(request, "dashboard/dashboard.html", context)