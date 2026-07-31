from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def restrict_to_roles(allowed_roles=[]):
    """Enforces server-side view routing based on the authenticated operator's role context."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
                
            role_obj = getattr(request.user, 'role', None)
            if not role_obj or not getattr(role_obj, 'role_name', None):
                if request.user.is_staff:
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("Your operating context lacks an assigned role.")
                
            current_user_role = role_obj.role_name.upper()
            normalized_allowed = [r.upper() for r in allowed_roles]
            
            # Match ADMIN and ADMINISTRATOR parameters safely
            if 'ADMIN' in normalized_allowed and 'ADMINISTRATOR' not in normalized_allowed:
                normalized_allowed.append('ADMINISTRATOR')
            if 'ADMINISTRATOR' in normalized_allowed and 'ADMIN' not in normalized_allowed:
                normalized_allowed.append('ADMIN')

            if current_user_role in normalized_allowed or request.user.is_staff:
                return view_func(request, *args, **kwargs)
                
            raise PermissionDenied("Your operating context lacks permission to access this resource.")
        return _wrapped_view
    return decorator