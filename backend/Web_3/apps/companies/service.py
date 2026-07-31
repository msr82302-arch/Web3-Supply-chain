# apps/companies/service.py
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.companies.models import Company, CompanyAddress, CompanyStatus, CompanyType
from apps.accounts.models import User

class CompanyService:
    @staticmethod
    @transaction.atomic
    def create_company_with_channels(company_data: dict, creator_user_id, addresses_data: list = None) -> Company:
        """Atomically boots an enterprise node alongside tracking coordinates and multi-tenant security layers."""
        if not creator_user_id:
            raise ValidationError("A valid authentication user identity context is required to spin up an organization.")

        # Wipe structural compliance injection properties from regular operations users
        company_data['is_verified'] = False
        company_data['status'] = CompanyStatus.PENDING

        requested_type = company_data.get('company_type', CompanyType.BUYER)
        if requested_type not in CompanyType.values:
            requested_type = CompanyType.BUYER
            company_data['company_type'] = requested_type

        # Deploy company base instance record
        company = Company.objects.create(**company_data)

        # Iterate and build unmanaged location tracking assets safely
        if addresses_data:
            for addr_payload in addresses_data:
                CompanyService._instantiate_address_safely(company, addr_payload)

        # Provision relationship directly on the standard user table
        User.objects.filter(user_id=creator_user_id).update(company=company)
        
        return company

    @staticmethod
    @transaction.atomic
    def update_company_profile(company: Company, profile_data: dict, locations_payload: list = None) -> Company:
        """Modifies core profile details securely while filtering out any hidden status injection overrides."""
        profile_data.pop('is_verified', None)
        profile_data.pop('status', None)
        profile_data.pop('company_id', None)

        for field, value in profile_data.items():
            setattr(company, field, value)
        company.save()

        if locations_payload is not None:
            CompanyAddress.objects.filter(company=company).delete()
            for addr_payload in locations_payload:
                CompanyService._instantiate_address_safely(company, addr_payload)
        return company

    @staticmethod
    @transaction.atomic
    def append_secure_address(company: Company, address_data: dict, executing_user_id) -> CompanyAddress:
        """Attaches an extra logistics asset point checking authorization flags beforehand."""
        try:
            user = User.objects.get(user_id=executing_user_id)
        except User.DoesNotExist:
            raise ValidationError("User not found.")

        # FIXED: Defensive getattr check for role and staff checks
        role_obj = getattr(user, 'role', None)
        role_name = getattr(role_obj, 'role_name', '').upper() if role_obj else ''
        is_admin = role_name in ['ADMIN', 'ADMINISTRATOR'] or getattr(user, 'is_staff', False)
        
        has_access = user.company == company and is_admin

        if not has_access:
            raise ValidationError("Execution Refusal: Account lacks administrative write privileges for this tenant.")
        return CompanyService._instantiate_address_safely(company, address_data)

    @staticmethod
    @transaction.atomic
    def transition_compliance_lifecycle(company: Company, target_status: str, authority_user) -> Company:
        """Advances network validation checkpoints. Restricted to global platform admins/auditors."""
        is_staff = getattr(authority_user, 'is_staff', False)
        is_superuser = getattr(authority_user, 'is_superuser', False)

        if not (is_superuser or is_staff):
            raise ValidationError("Access Denied: Administrative system authority required to alter compliance records.")

        if target_status not in CompanyStatus.values:
            raise ValidationError(f"Invalid transition state target choice: '{target_status}'.")

        company.status = target_status
        company.is_verified = (target_status == CompanyStatus.VERIFIED)
        company.save()
        return company

    @staticmethod
    def _instantiate_address_safely(company: Company, payload: dict) -> CompanyAddress:
        """Applies data cleaning techniques over coordinate rows to match unmanaged schemas without overflow."""
        lat = payload.get('latitude')
        lng = payload.get('longitude')
        payload.pop('company', None)
        payload.pop('address_id', None)

        if lat is not None:
            payload['latitude'] = CompanyService._sanitize_coordinate(lat)
        if lng is not None:
            payload['longitude'] = CompanyService._sanitize_coordinate(lng)
        return CompanyAddress.objects.create(company=company, **payload)

    @staticmethod
    def _sanitize_coordinate(value) -> Decimal:
        """
        Normalizes tracking data parameters to match exact PostgreSQL decimal layouts.
        Prevents overflow issues with unmanaged tables (max_digits=10, decimal_places=7).
        """
        if value is None or value == "":
            return None
        try:
            quantized = Decimal(str(value)).quantize(Decimal('1.0000000'))
            if abs(quantized) >= Decimal('1000.0000000'):
                raise ValidationError("Geospatial value out of scale limits for tracking definitions.")
            return quantized
        except (InvalidOperation, ValueError):
            raise ValidationError(f"Invalid decimal string formatting value structure: {value}")