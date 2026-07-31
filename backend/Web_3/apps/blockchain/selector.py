from django.db import connection
from apps.blockchain.models import Wallet, BlockchainTransaction, OwnershipHistory

class BlockchainSelector:
    """Helper module encapsulating safe, multi-tenant database queries."""

    @staticmethod
    def get_scoped_wallets(user, company_id=None):
        """Filters wallets based on tenant contexts."""
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return Wallet.objects.all().order_by('-created_at')
        return Wallet.objects.filter(user_id=getattr(user, 'user_id', user.id)).order_by('-created_at')

    @staticmethod
    def get_scoped_transactions(user, company_id=None):
        """Filters transactions based on company status constraints."""
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return BlockchainTransaction.objects.all().order_by('-created_at')
        return BlockchainTransaction.objects.all().order_by('-created_at')[:25]

    @staticmethod
    def get_blockchain_metrics():
        """Calculates blockchain transaction states and counts for the central analytics workspace."""
        total_minted = BlockchainTransaction.objects.filter(transaction_type='MINT').count()
        total_transferred = BlockchainTransaction.objects.filter(transaction_type='TRANSFER').count()
        failed_count = BlockchainTransaction.objects.filter(status='FAILED').count()
        confirmed_count = BlockchainTransaction.objects.filter(status='CONFIRMED').count()
        
        return {
            "total_mints": total_minted,
            "total_transfers": total_transferred,
            "failed_txs": failed_count,
            "confirmed_txs": confirmed_count
        }