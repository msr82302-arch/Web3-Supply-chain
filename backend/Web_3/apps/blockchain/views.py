from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import connection
from django.utils import timezone
import uuid

# Explicitly import SessionAuthentication to handle standard logged-in session cookies
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from apps.blockchain.models import Wallet, BlockchainTransaction, OwnershipHistory
from apps.blockchain.service import BlockchainService, is_valid_uuid
from apps.blockchain.permission import IsPlatformAdmin, get_user_role_name_raw
from apps.blockchain.serializer import WalletSerializer

def get_user_company_id_raw(user):
    """Direct lookup of current operator's company identifier."""
    user_id = getattr(user, 'user_id', getattr(user, 'id', None))
    if not user_id:
        return None
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT company_id FROM "supply_chain_schema"."users" WHERE user_id = %s LIMIT 1;', [str(user_id)])
            row = cursor.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
    return None

# ==============================================================================
# 1. FRONTEND TEMPLATE VIEWS (HTMX Fragments & Full Pages)
# ==============================================================================

@login_required
def wallet_list_html_view(request):
    """Renders all registered consortium wallets under active tenant isolation constraints."""
    from apps.blockchain.selector import BlockchainSelector
    wallets = BlockchainSelector.get_scoped_wallets(request.user)
    context = {
        'wallet_list': wallets,
        'breadcrumbs': [{'title': 'Consortium Wallets', 'url': '#'}]
    }
    return render(request, 'blockchain/wallet.html', context)


@login_required
def transaction_history_html_view(request):
    """Renders ledger transaction histories based on verification levels."""
    from apps.blockchain.selector import BlockchainSelector
    transactions = BlockchainSelector.get_scoped_transactions(request.user)
    context = {
        'transaction_list': transactions,
        'breadcrumbs': [{'title': 'Block Explorer Logs', 'url': '#'}]
    }
    # Matches your exact file name: transaction-history.html [2]
    return render(request, 'blockchain/transaction_history.html', context)


@login_required
def ownership_history_html_view(request):
    """Renders custody verification arrays."""
    transfers = OwnershipHistory.objects.select_related('product', 'blockchain_transaction').all().order_by('-transfer_date')
    context = {
        'ownership_list': transfers,
        'breadcrumbs': [{'title': 'Custody Audit Log', 'url': '#'}]
    }
    return render(request, 'blockchain/ownership.html', context)


@login_required
def nft_hub_html_view(request):
    """Renders digital twin structures categorized by consensus token types."""
    erc721_tokens = BlockchainTransaction.objects.filter(transaction_type='MINT').order_by('-created_at')
    erc20_history = BlockchainTransaction.objects.filter(transaction_type__in=['TRANSFER', 'PAYMENT']).order_by('-created_at')
    erc1155_history = BlockchainTransaction.objects.filter(transaction_type__in=['BATCH_MINT', 'BATCH_TRANSFER']).order_by('-created_at')
    
    context = {
        'mint_transactions': erc721_tokens,
        'erc20_transactions': erc20_history,
        'erc1155_transactions': erc1155_history,
        'breadcrumbs': [{'title': 'Asset Hub', 'url': '#'}]
    }
    return render(request, 'blockchain/nft.html', context)


# ==============================================================================
# 2. REST API CHALLENGE & VERIFICATION ENDPOINTS
# ==============================================================================

class WalletChallengeAPI(APIView):
    """Generates a secure cryptographic challenge nonce to sign."""
    permission_classes = [permissions.IsAuthenticated]
    # Enforces Session authentication so standard logged-in session cookies are checked
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get(self, request):
        challenge = BlockchainService.generate_auth_challenge(request.session)
        return Response({
            "status": "success",
            "challenge": challenge
        }, status=status.HTTP_200_OK)


class WalletVerifyAPI(APIView):
    """Verifies signature ownership and registers the wallet."""
    permission_classes = [permissions.IsAuthenticated]
    # Enforces Session authentication so standard logged-in session cookies are checked
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def post(self, request):
        wallet_address = request.data.get('wallet_address')
        signature = request.data.get('signature')
        wallet_provider = request.data.get('wallet_provider', 'MetaMask')
        blockchain_network = request.data.get('blockchain_network', 'Ethereum')

        if not wallet_address or not signature:
            return Response({
                "status": "error",
                "message": "Missing wallet signature proof parameters."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cryptographically verify the EIP-191 signature matches the session challenge
        is_valid = BlockchainService.verify_wallet_signature(request.session, wallet_address, signature)
        
        if is_valid:
            user_uuid = getattr(request.user, 'user_id', getattr(request.user, 'id', None))
            wallet_payload = {
                "wallet_address": wallet_address,
                "wallet_provider": wallet_provider,
                "blockchain_network": blockchain_network
            }
            wallet = BlockchainService.register_verified_wallet(user_uuid, wallet_payload)
            return Response({
                "status": "success",
                "message": "Cryptographic wallet proof successfully verified.",
                "data": WalletSerializer(wallet).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Signature validation failed. Challenge mismatch or replay detected."
        }, status=status.HTTP_401_UNAUTHORIZED)