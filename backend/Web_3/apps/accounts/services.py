# apps/accounts/services.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.accounts.models import User, Company, Role

logger = logging.getLogger('enterprise.accounts.services')

class StructuralOnboardingService:
    @staticmethod
    @transaction.atomic
    def execute_b2b_onboarding(cleaned_data: dict) -> User:
        """Atomically provisions a Company record and links the newly registered administrative User."""
        try:
            # 1. Instantiate the Company with verification flag set to True for active login support
            company = Company.objects.create(
                company_name=cleaned_data['company_name'],
                company_type=cleaned_data['company_type'],
                registration_number=cleaned_data['registration_number'],
                tax_number=cleaned_data['tax_number'],
                is_verified=True # Enable immediate login clearance
            )
            
            # 2. Match the exact operational Role row
            role_target = cleaned_data['company_type'].upper()
            role, _ = Role.objects.get_or_create(role_name=role_target)
            
            # 3. Create the account with email-based identity
            user = User.objects.create_user(
                email=cleaned_data['email'],      
                password=cleaned_data['password'],
                first_name=cleaned_data['first_name'],
                last_name=cleaned_data['last_name'],
                phone=cleaned_data.get('phone'),
                company=company,
                role=role
            )
            
            logger.info(f"Successfully onboarded Company: {company.company_id} with Admin Operator: {user.user_id}")
            return user
            
        except Exception as error:
            logger.error(f"Failed to execute B2B onboarding sequence: {str(error)}")
            raise ValidationError(f"B2B Onboarding sequence halted: {str(error)}")