

# Register your models here.
# apps/nft/admin.py
from django.contrib import admin
from apps.nft.models import NFT, Wallet

@admin.register(NFT)
class NFTAdmin(admin.ModelAdmin):
    list_display = ('nft_id', 'product', 'token_id', 'contract_address', 'minted_at')
    search_fields = ('contract_address', 'ipfs_hash', 'token_id')
    list_filter = ('minted_at',)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('wallet_id', 'user_id', 'wallet_address', 'is_active', 'created_at')
    search_fields = ('wallet_address', 'user_id')