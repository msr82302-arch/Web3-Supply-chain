import re
from rest_framework import serializers
from apps.blockchain.models import Wallet, BlockchainTransaction

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['wallet_id', 'user_id', 'wallet_address', 'blockchain_network', 'wallet_provider', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['is_verified']

    def validate_wallet_address(self, value):
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            raise serializers.ValidationError("Invalid cryptographic hex address signature format.")
        return value


class BlockchainTransactionSerializer(serializers.ModelSerializer):
    gas_fee = serializers.DecimalField(max_digits=18, decimal_places=8)

    class Meta:
        model = BlockchainTransaction
        fields = ['transaction_id', 'nft_id', 'transaction_hash', 'block_number', 'network', 'gas_fee', 'transaction_type', 'status', 'created_at']

    def validate_transaction_hash(self, value):
        if not re.match(r'^0x[a-fA-F0-9]{64}$', value):
            raise serializers.ValidationError("Malformed cryptographic ledger transaction hash.")
        return value