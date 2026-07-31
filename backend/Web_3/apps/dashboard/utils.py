import os
import json
import logging
from django.conf import settings
from apps.sys_setting.service import SystemSettingsService

logger = logging.getLogger(__name__)

# Lazy import of web3 to handle environments without pre-installed bin-packages
try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPoAMiddleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

class Web3ClientManager:
    """Centralized client managing active RPC endpoints, smart contract ABIs and secure backend web3 connections."""
    
    @classmethod
    def get_web3_client(cls):
        """Builds a secure Web3 client utilizing parameters from the central System Settings registry."""
        if not WEB3_AVAILABLE:
            logger.warning("[WEB3_CLIENT] web3.py library is not installed in the environment.")
            return None

        # Dynamically load RPC and Network configs from System Settings [2]
        settings_data = SystemSettingsService.get_latest_settings()
        rpc_url = getattr(settings_data, 'blockchain_rpc_url', None) or os.getenv("BLOCKCHAIN_RPC_URL")
        
        if not rpc_url:
            logger.info("[WEB3_CLIENT] No RPC URL configured. Running in simulated ledger sandbox mode.")
            return None

        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Auto-inject middleware for Proof of Authority (PoA) compatibility (e.g. Goerli, Polygon)
            w3.middleware_onion.inject(ExtraDataToPoAMiddleware, layer=0)
            
            if w3.is_connected():
                return w3
            logger.warning(f"[WEB3_CLIENT] Unable to connect to RPC node: {rpc_url}")
        except Exception as e:
            logger.error(f"[WEB3_CLIENT] Exception occurred during provider initialization: {str(e)}")
        
        return None

    @classmethod
    def get_contract_abi(cls, contract_name):
        """Loads secure JSON contract ABIs from local paths."""
        abi_dir = os.path.join(settings.BASE_DIR, 'apps', 'blockchain', 'abi')
        abi_path = os.path.join(abi_dir, f"{contract_name}.json")
        if os.path.exists(abi_path):
            with open(abi_path, 'r') as f:
                return json.load(f)
        return []