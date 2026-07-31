from rest_framework import permissions
from django.db import connection

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

class IsPlatformAdmin(permissions.BasePermission):
    """Restricts operations to platform administrators or superusers."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Safe check of attributes that may be missing on custom User models
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
            return True
        
        role_name = get_user_role_name_raw(request.user)
        return role_name in ['Administrator', 'Platform Administrator']