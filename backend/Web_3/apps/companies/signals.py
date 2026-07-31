# apps/accounts/signals.py
import logging
from django.db.models.signals import post_save, pre_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import connections

logger = logging.getLogger('apps.accounts.signals')
User = get_user_model()

@receiver(pre_migrate)
def create_unmanaged_tables_pre_migrate(sender, **kwargs):
    """
    Creates custom supply_chain_schema and unmanaged companies/roles/users tables
    prior to executing any migrations to prevent foreign-key reference crashes.
    """
    if sender.name == 'apps.accounts':
        connection = connections[kwargs.get('using', 'default')]
        with connection.cursor() as cursor:
            # 1. Create custom supply chain schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS supply_chain_schema;")
            
            # 2. Create unmanaged companies table (Fully aligned with all 13 columns)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supply_chain_schema.companies (
                    company_id UUID PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    company_type VARCHAR(100),
                    registration_number VARCHAR(100) UNIQUE,
                    tax_number VARCHAR(100) UNIQUE,
                    email VARCHAR(255),
                    phone VARCHAR(30),
                    website VARCHAR(255),
                    logo_url TEXT,
                    is_verified BOOLEAN DEFAULT FALSE,
                    status VARCHAR(20) DEFAULT 'PENDING',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 3. Create unmanaged roles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supply_chain_schema.roles (
                    role_id UUID PRIMARY KEY,
                    role_name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 4. Create unmanaged users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supply_chain_schema.users (
                    user_id UUID PRIMARY KEY,
                    company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE SET NULL,
                    role_id UUID REFERENCES supply_chain_schema.roles(role_id) ON DELETE RESTRICT,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    phone VARCHAR(30),
                    profile_image TEXT,
                    is_email_verified BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_staff BOOLEAN DEFAULT FALSE,
                    last_login TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. Create unmanaged company_addresses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supply_chain_schema.company_addresses (
                    address_id UUID PRIMARY KEY,
                    company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE CASCADE,
                    country VARCHAR(100) NOT NULL,
                    state VARCHAR(100),
                    city VARCHAR(100) NOT NULL,
                    postal_code VARCHAR(20),
                    street_address TEXT NOT NULL,
                    latitude DECIMAL(10, 7),
                    longitude DECIMAL(10, 7),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 6. Create unmanaged company_user_roles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supply_chain_schema.company_user_roles (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL,
                    company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    is_company_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, company_id)
                );
            """)
            logger.info("Successfully provisioned custom schema and unmanaged reference tables.")


try:
    from services.email_service import EnterpriseEmailService
except ImportError:
    class EnterpriseEmailService:
        @staticmethod
        def dispatch_transactional_template(template_name, context, recipient_email, subject_line):
            from django.core.mail import send_mail
            message = f"Verify your email at: token={context['activate_token']}&uid={context['uid']}"
            send_mail(subject_line, message, 'no-reply@platform.com', [recipient_email])

@receiver(post_save, sender=User)
def trigger_onboarding_verification(sender, instance, created, **kwargs):
    """
    Fires automatically upon fresh user creation node initialization
    """
    if created:  
        context = {
            "first_name": instance.first_name or "Operator",
            "activate_token": getattr(instance, 'profile_token', 'default-token-hash'),
            "uid": str(instance.user_id)
        }
        try:
            EnterpriseEmailService.dispatch_transactional_template(
                template_name="verify-email.html", 
                context=context,
                recipient_email=instance.email,
                subject_line="Action Required: Verify Account Interface Link"
            )
        except Exception as e:
            logger.error(f"Failed to dispatch onboarding email verification: {str(e)}")