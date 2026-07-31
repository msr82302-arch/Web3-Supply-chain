import uuid
from django.utils import timezone
from django.db import connection
from .models import SystemSetting

def is_valid_uuid(val):
    """Utility function to safely check if a value is a valid UUID string format."""
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

class SystemSettingsService:
    @staticmethod
    def get_latest_settings():
        """Fetches global SaaS operator configurations, creating a fallback row if missing."""
        setting = SystemSetting.objects.all().order_by('id').first()
        if not setting:
            setting = SystemSetting.objects.create(application_name='Web3 Supply Chain SaaS')
        return setting

    @classmethod
    def update_settings_block(cls, user, validated_data, section_name="General"):
        """Saves config settings and writes a tracking trace to the audit logging ledger."""
        setting = cls.get_latest_settings()
        
        # Clean and safely validate input matching UUID columns to avoid database crashes
        for key, value in validated_data.items():
            if key in ['updated_by', 'created_by', 'default_wallet'] and value:
                if not is_valid_uuid(value):
                    continue  # Safely ignore values that are not valid UUID strings
            setattr(setting, key, value)
            
        user_uuid = getattr(user, 'user_id', getattr(user, 'id', None))
        
        if user_uuid and is_valid_uuid(user_uuid):
            setting.updated_by = str(user_uuid)
        else:
            setting.updated_by = None
            
        setting.updated_at = timezone.now()
        setting.save()

        # Write audit trail directly to the tracking database log table
        with connection.cursor() as cursor:
            try:
                log_user = str(user_uuid) if (user_uuid and is_valid_uuid(user_uuid)) else "00000000-0000-0000-0000-000000000000"
                cursor.execute(
                    """
                    INSERT INTO "supply_chain_schema"."audit_logs" (user_id, action, created_at)
                    VALUES (%s, %s, NOW());
                    """, 
                    [log_user, f"Updated System Settings Profile Section: {section_name}"]
                )
            except Exception:
                pass  # Bypassed to maintain thread stability if audit tables are in flux

        return setting