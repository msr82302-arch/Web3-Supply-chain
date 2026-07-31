# apps/accounts/signals.py
import logging
from django.db.models.signals import post_save, pre_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import connections

logger = logging.getLogger('apps.accounts.signals')
User = get_user_model()

# Global tracking sentinel to ensure SQL runs exactly once before any migrations
_unmanaged_tables_created = False

@receiver(pre_migrate)
def create_unmanaged_tables_pre_migrate(sender, **kwargs):
    """
    Creates custom supply_chain_schema and unmanaged SCM tables
    prior to executing any migrations to prevent foreign-key reference crashes.
    Runs exactly once on the first pre_migrate signal of any application.
    """
    global _unmanaged_tables_created
    if _unmanaged_tables_created:
        return

    connection = connections[kwargs.get('using', 'default')]
    with connection.cursor() as cursor:
        # 1. Create custom supply chain schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS supply_chain_schema;")
        
        # 2. Create unmanaged companies table
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
                -- is_active is deliberately omitted to maintain database schema compliance
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
                -- matches exact pgAdmin columns list
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

        # 7. Create unmanaged product_categories table
        # FIXED: Added description text column to align with PostgreSQL production schema [1]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.product_categories (
                category_id UUID PRIMARY KEY,
                category_name VARCHAR(150) NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 8. Create unmanaged products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.products (
                product_id UUID PRIMARY KEY,
                manufacturer_company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE CASCADE,
                category_id UUID REFERENCES supply_chain_schema.product_categories(category_id) ON DELETE RESTRICT,
                product_name VARCHAR(255) NOT NULL,
                sku VARCHAR(100),
                serial_number VARCHAR(100),
                batch_number VARCHAR(100),
                manufacture_date DATE,
                expiry_date DATE,
                description TEXT,
                current_status VARCHAR(50) NOT NULL,
                qr_code TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 9. Create unmanaged product_status_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.product_status_history (
                history_id UUID PRIMARY KEY,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE CASCADE,
                changed_by UUID NOT NULL,
                old_status VARCHAR(50),
                new_status VARCHAR(50) NOT NULL,
                remarks TEXT,
                changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 10. Create unmanaged nfts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.nfts (
                nft_id UUID PRIMARY KEY,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE RESTRICT,
                token_id BIGINT NOT NULL,
                contract_address VARCHAR(255) NOT NULL,
                ipfs_hash TEXT NOT NULL,
                metadata_uri TEXT NOT NULL,
                minted_by UUID NOT NULL,
                minted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 11. Create unmanaged ownership_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.ownership_history (
                ownership_id UUID PRIMARY KEY,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE CASCADE,
                previous_owner VARCHAR(255),
                current_owner VARCHAR(255) NOT NULL,
                blockchain_transaction VARCHAR(255),
                transfer_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                remarks TEXT
            );
        """)

        # 12. Create unmanaged wallets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.wallets (
                wallet_id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                wallet_address VARCHAR(42) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 13. Create unmanaged orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.orders (
                order_id UUID PRIMARY KEY,
                buyer_company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE RESTRICT,
                seller_company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE RESTRICT,
                order_number VARCHAR(100) NOT NULL,
                total_amount DECIMAL(15, 2) NOT NULL,
                order_status VARCHAR(50) NOT NULL,
                order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expected_delivery DATE
            );
        """)

        # 14. Create unmanaged order_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.order_items (
                order_item_id UUID PRIMARY KEY,
                order_id UUID REFERENCES supply_chain_schema.orders(order_id) ON DELETE CASCADE,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE RESTRICT,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(12, 2) NOT NULL,
                subtotal DECIMAL(15, 2) NOT NULL
            );
        """)

        # 15. Create unmanaged shipments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.shipments (
                shipment_id UUID PRIMARY KEY,
                order_id UUID REFERENCES supply_chain_schema.orders(order_id) ON DELETE RESTRICT,
                logistics_company_id UUID REFERENCES supply_chain_schema.companies(company_id) ON DELETE RESTRICT,
                shipment_number VARCHAR(100) NOT NULL,
                tracking_number VARCHAR(100),
                shipment_status VARCHAR(50) NOT NULL,
                departure_date TIMESTAMP WITH TIME ZONE,
                expected_arrival DATE,
                actual_arrival DATE
            );
        """)

        # 16. Create unmanaged shipment_tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.shipment_tracking (
                tracking_id UUID PRIMARY KEY,
                shipment_id UUID REFERENCES supply_chain_schema.shipments(shipment_id) ON DELETE CASCADE,
                latitude DECIMAL(10, 7) NOT NULL,
                longitude DECIMAL(10, 7) NOT NULL,
                location VARCHAR(255) NOT NULL,
                tracking_status VARCHAR(100) NOT NULL,
                recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 17. Create unmanaged notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.notifications (
                notification_id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 18. Create unmanaged ai_analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.ai_analysis (
                analysis_id UUID PRIMARY KEY,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE CASCADE,
                analyzed_by UUID NOT NULL,
                analysis_type VARCHAR(100) NOT NULL,
                prediction TEXT NOT NULL,
                confidence_score DECIMAL(5, 2) NOT NULL,
                model_name VARCHAR(150) NOT NULL,
                model_version VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 19. Create unmanaged audit_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.audit_logs (
                audit_log_id UUID PRIMARY KEY,
                user_id UUID,
                action VARCHAR(100) NOT NULL,
                entity_name VARCHAR(100) NOT NULL,
                entity_id UUID NOT NULL,
                old_values JSONB,
                new_values JSONB,
                ip_address VARCHAR(100),
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 20. Create unmanaged fraud_reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.fraud_reports (
                report_id UUID PRIMARY KEY,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE RESTRICT,
                reported_by UUID NOT NULL,
                ai_analysis_id UUID REFERENCES supply_chain_schema.ai_analysis(analysis_id) ON DELETE SET NULL,
                fraud_score DECIMAL(5, 2) NOT NULL,
                fraud_level VARCHAR(50) NOT NULL,
                report_status VARCHAR(50) NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP WITH TIME ZONE
            );
        """)

        # 21. Create unmanaged qr_codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.qr_codes (
                qr_id UUID PRIMARY KEY,
                product_id UUID REFERENCES supply_chain_schema.products(product_id) ON DELETE RESTRICT,
                qr_code TEXT NOT NULL,
                qr_image_url TEXT NOT NULL,
                verification_url TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 22. Create unmanaged verification_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_schema.verification_logs (
                verification_log_id UUID PRIMARY KEY,
                qr_id UUID REFERENCES supply_chain_schema.qr_codes(qr_id) ON DELETE RESTRICT,
                verified_by UUID,
                ip_address VARCHAR(100),
                device_info TEXT,
                country VARCHAR(100),
                city VARCHAR(100),
                latitude DECIMAL(10, 7),
                longitude DECIMAL(10, 7),
                verification_result VARCHAR(50) NOT NULL,
                verified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Successfully provisioned custom SCM ledger unmanaged schemas.")


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