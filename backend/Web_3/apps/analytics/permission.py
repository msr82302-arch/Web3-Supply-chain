# apps/analytics/permissions.py
from rest_framework import permissions

class IsAuditLogAuthorized(permissions.BasePermission):
    """
    Blocks normal operational users from inspecting system logs.
    Restricted to auditors, global platform administrators, and staff.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
            return True
            
        role_name = getattr(request.user.role, 'role_name', '').upper() if request.user.role else ''
        return role_name in ['AUDITOR', 'ADMIN', 'ADMINISTRATOR']