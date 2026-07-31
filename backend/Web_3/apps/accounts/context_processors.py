def inject_rbac_context(request):
    """Automatically provides multi-tenant and role values to all template templates."""
    if request.user.is_authenticated:
        role_obj = getattr(request.user, 'role', None)
        role_name = getattr(role_obj, 'role_name', '').upper() if role_obj else ''
        return {
            'GLOBAL_COMPANY': getattr(request.user, 'company', None),
            'GLOBAL_ROLE': role_name,
            'IS_MANUFACTURER': role_name == 'MANUFACTURER',
            'IS_LOGISTICS': role_name == 'LOGISTICS',
            'IS_BUYER': role_name == 'BUYER',
            'IS_AUDITOR': role_name == 'AUDITOR',
        }
    return {}