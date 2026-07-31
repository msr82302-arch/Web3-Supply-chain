# apps/nft/serializers.py
from rest_framework import serializers
from apps.nft.models import NFT
from apps.blockchain.models import OwnershipHistory

class NFTSerializer(serializers.ModelSerializer):
    token_id = serializers.IntegerField(min_value=0)

    class Meta:
        model = NFT
        fields = ['nft_id', 'product', 'token_id', 'contract_address', 'ipfs_hash', 'metadata_uri', 'minted_by', 'minted_at']
        # FIXED: Enforce read-only constraint to prevent identity spoofing
        read_only_fields = ['nft_id', 'minted_by', 'minted_at']


class OwnershipHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnershipHistory
        fields = ['ownership_id', 'product', 'previous_owner', 'current_owner', 'blockchain_transaction', 'transfer_date', 'remarks']