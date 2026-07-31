from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import connection
from django.utils import timezone
import uuid

from apps.sys_setting.models import SystemSetting

from apps.sys_setting.service import SystemSettingsService,is_valid_uuid
from apps.sys_setting.permission import IsPlatformAdmin,get_user_role_name_raw
    
from apps.sys_setting.serializer import(
    GeneralSettingsSerializer,
    SecuritySettingsSerializer,
    NotificationSettingsSerializer,
    BlockchainSettingsSerializer,
    APISettingsSerializer
)





def get_user_company_id_raw(user):
    """Direct lookup of current operator's company identifier."""
    user_id = getattr(user, 'user_id', getattr(user, 'id', None))
    if not user_id:
        return None
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT company_id FROM "supply_chain_schema"."users" WHERE user_id = %s LIMIT 1;', [str(user_id)])
            row = cursor.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
    return None

# ==============================================================================
# 1. FRONTEND TEMPLATE VIEWS (HTMX Fragments & Full Pages)
# ==============================================================================

@login_required
def settings_dashboard_view(request):
    """Renders base application engine administration frames."""
    role = get_user_role_name_raw(request.user)
    
    # Safe check of attributes that may be missing on custom User models
    is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or (role in ['Administrator', 'Platform Administrator'])
    is_company_admin = role == 'Company Administrator'
    
    if not (is_admin or is_company_admin):
        # Maps directly to sys-settings/permission-denied.html [2]
        return render(request, "sys-settings/permission-denied.html", status=403)
        
    settings_data = SystemSettingsService.get_latest_settings()
    context = {"settings": settings_data, "active_tab": "general"}
    # Maps directly to sys-settings/general-dashboard.html [2]
    return render(request, "sys-settings/general-dashboard.html", context)

@login_required
def load_settings_tab(request, tab_name):
    """Dynamically streams separate view fragments across HTMX triggers without full page reload cycles."""
    role = get_user_role_name_raw(request.user)
    
    # Safe check of attributes that may be missing on custom User models
    is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or (role in ['Administrator', 'Platform Administrator'])
    is_company_admin = role == 'Company Administrator'
    
    if not (is_admin or is_company_admin):
        # Maps directly to sys-settings/permission-denied.html [2]
        return render(request, "sys-settings/permission-denied.html", status=403)

    settings_data = SystemSettingsService.get_latest_settings()
    context = {"settings": settings_data}
    company_id = get_user_company_id_raw(request.user)

    with connection.cursor() as cursor:
        try:
            if tab_name == "users":
                if is_admin:
                    cursor.execute('SELECT user_id, first_name, last_name, email, is_active FROM "supply_chain_schema"."users" ORDER BY created_at DESC LIMIT 50;')
                else:
                    cursor.execute('SELECT user_id, first_name, last_name, email, is_active FROM "supply_chain_schema"."users" WHERE company_id = %s ORDER BY created_at DESC LIMIT 50;', [str(company_id)])
                columns = [col[0] for col in cursor.description]  # Correct mapping to column name strings [5]
                context["records"] = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            elif tab_name == "roles":
                cursor.execute('SELECT role_id, role_name, description FROM "supply_chain_schema"."roles" ORDER BY role_name ASC;')
                columns = [col[0] for col in cursor.description]  # Correct mapping to column name strings [5]
                context["records"] = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            elif tab_name == "audit_logs" or tab_name == "audit-logs":
                if is_admin:
                    cursor.execute('SELECT id, user_id, action, created_at FROM "supply_chain_schema"."audit_logs" ORDER BY created_at DESC LIMIT 100;')
                else:
                    cursor.execute(
                        'SELECT id, user_id, action, created_at FROM "supply_chain_schema"."audit_logs" '
                        'WHERE user_id::uuid IN (SELECT user_id FROM "supply_chain_schema"."users" WHERE company_id = %s) '
                        'ORDER BY created_at DESC LIMIT 100;',
                        [str(company_id)]
                    )
                columns = [col[0] for col in cursor.description]  # Correct mapping to column name strings [5]
                context["records"] = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception:
            context["records"] = []

    # Map the requested tabs to the exact template file names on your disk [2]
    template_map = {
        "general": "setting",          # Maps general tab to setting.html (your active form) [2]
        "security": "security",        # Maps to security.html [2]
        "notifications": "notifications", # Maps to notifications.html [2]
        "blockchain": "blockchain",    # Maps to blockchain.html [2]
        "api-keys": "api-keys",        # Maps to api-keys.html [2]
        "users": "users",              # Maps to users.html [2]
        "roles": "roles",              # Maps to roles.html [2]
        "audit_logs": "audit-logs",    # Maps underscore to hyphen audit-logs.html [2]
        "audit-logs": "audit-logs",    # Maps hyphen audit-logs.html [2]
    }
    
    file_name = template_map.get(tab_name, tab_name)
    target_template = f"sys-settings/{file_name}.html"  # Prepends your exact templates folder name [2]
    return render(request, target_template, context)

# ==============================================================================
# 2. REST API DATA PROCESSING ENDPOINTS
# ==============================================================================

class BaseSettingsAPI(APIView):
    permission_classes = [IsPlatformAdmin]  # Only Platform Admins can modify global settings!
    serializer_class = None
    section_title = "System"

    def put(self, request):
        config = SystemSettingsService.get_latest_settings()
        payload_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        user_uuid = getattr(request.user, 'user_id', getattr(request.user, 'id', None))

        if user_uuid and len(str(user_uuid)) >= 32:
            payload_data['updated_by'] = str(user_uuid)
        else:
            payload_data.pop('updated_by', None)

        serializer = self.serializer_class(config, data=payload_data, partial=True)
        if serializer.is_valid():
            updated_record = SystemSettingsService.update_settings_block(
                user=request.user,
                validated_data=serializer.validated_data,
                section_name=self.section_title
            )
            # Standard wrapper format matching Alpine.js expectations [8]
            return Response({
                "status": "success",
                "message": f"{self.section_title} committed successfully.",
                "data": self.serializer_class(updated_record).data
            }, status=status.HTTP_200_OK)
            
        return Response({
            "status": "error",
            "message": "Input configuration validation failed.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class GeneralSettingsAPI(BaseSettingsAPI):
    serializer_class = GeneralSettingsSerializer
    section_title = "General Configurations"

class SecuritySettingsAPI(BaseSettingsAPI):
    serializer_class = SecuritySettingsSerializer
    section_title = "Security Rules"

class NotificationSettingsAPI(BaseSettingsAPI):
    serializer_class = NotificationSettingsSerializer
    section_title = "Notification Gateways"

class BlockchainSettingsAPI(BaseSettingsAPI):
    serializer_class = BlockchainSettingsSerializer
    section_title = "Web3 / Blockchain Core"

class APISettingsAPI(BaseSettingsAPI):
    serializer_class = APISettingsSerializer
    section_title = "Integration APIs"

# ==============================================================================
# 3. SECURED VISUAL EMAIL DEVELOPER PREVIEW ENDPOINTS
# ==============================================================================

@login_required
def preview_verify_email_template(request):
    """Protected visual onboarding template development endpoint."""
    role = get_user_role_name_raw(request.user)
    is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or role in ['Administrator', 'Platform Administrator']
    if not is_admin:
        return render(request, "sys-settings/permission-denied.html", status=403)
    context = {
        "first_name": getattr(request.user, 'first_name', "Operator-Alpha"),
        "activate_token": "cb0382a9-c4ef-4f97-a5f3-98ab828dc591",
        "uid": "MTI"
    }
    return render(request, "emails/verify-email.html", context)

@login_required
def preview_password_reset_template(request):
    """Protected credential recovery development preview."""
    role = get_user_role_name_raw(request.user)
    is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or role in ['Administrator', 'Platform Administrator']
    if not is_admin:
        return render(request, "sys-settings/permission-denied.html", status=403)
    context = {
        "first_name": getattr(request.user, 'first_name', "Terminal-Controller"),
        "token": "a5f398ab-828d-c591-cb03-82a9c4ef4f97",
        "uid": "MTI"
    }
    return render(request, "emails/reset-pass.html", context)

@login_required
def preview_shipment_notification_template(request):
    """Protected shipment movement tracking alert visual layout."""
    role = get_user_role_name_raw(request.user)
    is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or role in ['Administrator', 'Platform Administrator']
    if not is_admin:
        return render(request, "sys-settings/permission-denied.html", status=403)
    context = {
        "shipment_id": 101,
        "shipment_number": "SHP-2026-NEXUS-089",
        "tracking_status": "Customs Clearance & Validation",
        "location": "Port of Rotterdam Warehouse Terminal B, Netherlands",
        "recorded_at": timezone.now()
    }
    return render(request, "emails/shipment_notification.html", context)

@login_required
def preview_invoice_template(request):
    """Protected visual order receipt layouts template representation."""
    role = get_user_role_name_raw(request.user)
    is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or role in ['Administrator', 'Platform Administrator']
    if not is_admin:
        return render(request, "sys-settings/permission-denied.html", status=403)
    context = {
        "order_id": 405,
        "order_number": "ORD-GENESIS-7731",
        "buyer_name": "LMS Global Logistics Consortium",
        "seller_name": "Ecosystem Distribution Manufacturing Ltd.",
        "gross_total": 14250.00,
        "items_list": [
            {"product_name": "Decentralized Tracking Asset Tags (ERC-1155)", "quantity": 500, "unit_price": 12.00, "subtotal": 6000.00},
            {"product_name": "Secure Cryptographic Smart Sensor Hubs", "quantity": 25, "unit_price": 310.00, "subtotal": 7750.00},
            {"product_name": "Network Access Node Licensing Protocols", "quantity": 10, "unit_price": 50.00, "subtotal": 500.00}
        ]
    }
    return render(request, "emails/invoice.html", context)