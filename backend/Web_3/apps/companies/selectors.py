# apps/companies/selectors.py
from django.db.models import Q
from apps.companies.models import Company, CompanyStatus

class UserCompanyRoleContext:
    def __init__(self, is_member, is_company_admin):
        self.is_member = is_member
        self.is_company_admin = is_company_admin


class CompanySelector:
    @staticmethod
    def get_visible_companies(user):
        """
        Enforces clear multi-tenant data boundaries:
        - System superusers/global staff can access all profiles.
        - Regular company members can view their own company profile (even if pending).
        - Registered participants can view public details of other verified active companies.
        """
        if not user or user.is_anonymous:
            return Company.objects.none()
            
        # Safe getattr mapping for superuser check
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return Company.objects.all()

        # FIXED: Extract the user's company directly from their model attributes to avoid non-existent table query
        user_company = getattr(user, 'company', None)
        user_company_ids = [user_company.company_id] if user_company else []

        return Company.objects.filter(
            Q(company_id__in=user_company_ids) | Q(status=CompanyStatus.VERIFIED)
        ).distinct()

    @staticmethod
    def get_user_role_context(user_or_id, company_id) -> UserCompanyRoleContext:
        """Retrieves membership permissions context directly from user model relationships."""
        from apps.accounts.models import User
        if isinstance(user_or_id, User):
            user = user_or_id
        else:
            try:
                user = User.objects.get(user_id=user_or_id)
            except User.DoesNotExist:
                return None

        user_company = getattr(user, 'company', None)
        if not user_company or str(user_company.company_id) != str(company_id):
            return None

        # Resolve admin status directly from native unmanaged role fields
        role_obj = getattr(user, 'role', None)
        role_name = getattr(role_obj, 'role_name', '').upper() if role_obj else ''
        is_admin = role_name in ['ADMIN', 'ADMINISTRATOR'] or getattr(user, 'is_staff', False)

        return UserCompanyRoleContext(is_member=True, is_company_admin=is_admin)