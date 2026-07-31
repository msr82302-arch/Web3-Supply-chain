from rest_framework import serializers
from .models import SystemSetting

class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = [
            'application_name', 'company_name', 'company_email', 'company_phone', 
            'company_address', 'company_logo', 'company_website', 'timezone', 
            'language', 'currency', 'date_format', 'theme', 'maintenance_mode', 'allow_registration'
        ]


class SecuritySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['email_verification', 'openai_enabled', 'updated_by', 'updated_at']


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['enable_notifications', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_email', 'smtp_use_tls']


class BlockchainSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = [
            'enable_blockchain', 'blockchain_network', 'blockchain_rpc_url', 
            'explorer_url', 'nft_contract_address', 'erc20_contract_address', 
            'erc1155_contract_address', 'default_wallet'
        ]


class APISettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['openai_enabled', 'ipfs_provider', 'storage_provider']