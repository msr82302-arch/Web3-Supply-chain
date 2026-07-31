# apps/companies/permissions.py
from rest_framework import permissions
from apps.companies.selectors import CompanySelector

class IsCompanyNetworkParticipant(permissions.BasePermission):
    """
    Enforces strict organizational multi-tenant security filters:
    - Allows platform superusers/staff complete operational capability.
    - Limits destructive and update changes (PUT/PATCH/DELETE) to designated corporate admins.
    - Grants read access to unverified companies for their own workspace data, 
      and to verified active companies across the global public network.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # FIXED: Defensive getattr check for administrative user lookup
        is_super = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
        if is_super:
            return True

        role_ctx = CompanySelector.get_user_role_context(request.user.user_id, obj.company_id)

        # Handle data modification actions (Write permissions)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return role_ctx is not None and getattr(role_ctx, 'is_company_admin', False)

        # Handle read operations (Safe GET requests)
        if request.method in permissions.SAFE_METHODS:
            # Grant access if user belongs to this company partition space
            if role_ctx is not None:
                return True
            # Otherwise, allow viewing only if the target company is verified active
            return obj.status == 'VERIFIED'

        return False