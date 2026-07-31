from django.apps import AppConfig

class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.blockchain'

    def ready(self):
        """
        Initializes distributed cryptographic ledger mutation monitoring updates on runtime boot.
        Handles: NFT Minted, Ownership Transfer, Verification Complete triggers.
        """
        import apps.blockchain.signals
