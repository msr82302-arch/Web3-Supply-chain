# apps/nft/views.py
import uuid
import secrets
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from eth_account.messages import encode_defunct
from eth_account import Account

from apps.nft.models import NFT, Wallet
from apps.products.models import Product
from apps.products.selectors import ProductSelector
from apps.blockchain.models import OwnershipHistory
from apps.nft.serializer import NFTSerializer, OwnershipHistorySerializer
from apps.nft.service import NFTService
from apps.nft.selector import NFTSelector

class NFTViewSet(viewsets.ModelViewSet):
    """Primary ledger entry checkpoint for product digital twins."""
    permission_classes = [IsAuthenticated]
    serializer_class = NFTSerializer

    def get_queryset(self):
        return NFTSelector.get_visible_nfts(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Enforce secure server-side minter assignment
        validated_data['minted_by'] = request.user.user_id
        
        try:
            nft = NFTService.record_minted_twin(validated_data)
            return Response(NFTSerializer(nft).data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OwnershipHistoryViewSet(viewsets.ModelViewSet):
    """Monitors historical custody chains and verified digital product handoffs."""
    queryset = OwnershipHistory.objects.all()
    serializer_class = OwnershipHistorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transfer = NFTService.record_ownership_transfer(serializer.validated_data)
        return Response(OwnershipHistorySerializer(transfer).data, status=status.HTTP_201_CREATED)


# =========================================================================
# WEB3 METAMASK CRYPTOGRAPHIC SIGNATURE CHALLENGE CHANNELS
# =========================================================================

def wallet_challenge_api(request):
    """Generates a secure UUIDv4 challenge nonce to prevent signature replay attacks."""
    nonce = secrets.token_hex(16)
    request.session['wallet_challenge_nonce'] = nonce
    challenge_msg = (
        f"SCM Platform Node wants you to verify your identity.\n\n"
        f"Challenge Nonce Token: {nonce}\n"
        f"Do not share this key with anyone."
    )
    return JsonResponse({"challenge": challenge_msg, "nonce": nonce})


def wallet_verify_api(request):
    """Recovers the signing address to verify ownership and prevent replay attacks."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    wallet_address = request.POST.get('wallet_address')
    signature = request.POST.get('signature')
    session_nonce = request.session.get('wallet_challenge_nonce')

    if not wallet_address or not signature or not session_nonce:
        return JsonResponse({"error": "Missing challenge validation parameters"}, status=status.HTTP_400_BAD_REQUEST)

    # Reconstruct challenge string
    challenge_msg = (
        f"SCM Platform Node wants you to verify your identity.\n\n"
        f"Challenge Nonce Token: {session_nonce}\n"
        f"Do not share this key with anyone."
    )

    # Cryptographically recover address from signature
    try:
        message = encode_defunct(text=challenge_msg)
        recovered_address = Account.recover_message(message, signature=signature)
    except Exception as e:
        return JsonResponse({"error": f"Invalid signature format: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    if recovered_address.lower() != wallet_address.lower():
        return JsonResponse({"error": "Cryptographic signature verification failed"}, status=status.HTTP_400_BAD_REQUEST)

    # Invalidate challenge nonce
    del request.session['wallet_challenge_nonce']
    
    # Save the verified wallet to the session
    request.session['verified_wallet_address'] = recovered_address.lower()
    return JsonResponse({"success": True, "wallet_address": recovered_address})


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

@login_required
def nft_list_html_view(request):
    """Renders active company digital twin NFTs available inside the user's session."""
    nfts = NFTSelector.get_visible_nfts(request.user)
    context = {
        'nft_list': nfts,
        'breadcrumbs': [{'title': 'Digital Twin Certificates', 'url': '#'}]
    }
    return render(request, 'nft/nft_list.html', context)


@login_required
def nft_detail_html_view(request, nft_id):
    """Renders detailed audit spec profiles for specific minted digital twins."""
    visible = NFTSelector.get_visible_nfts(request.user)
    nft = get_object_or_404(visible, nft_id=nft_id)
    context = {
        'nft': nft,
        'breadcrumbs': [
            {'title': 'Digital Twin Certificates', 'url': '/nft/'},
            {'title': 'Audit Specifications', 'url': '#'}
        ]
    }
    return render(request, 'nft/nft_detail.html', context)


@login_required
def nft_mint_html_view(request, product_id):
    """Renders the MetaMask signing and minting workspace for a product."""
    visible_products = ProductSelector.get_visible_products(request.user)
    product = get_object_or_404(visible_products, product_id=product_id)

    # Block minting if the product is already tokenized
    if NFT.objects.filter(product=product).exists():
        messages.error(request, "This commodity node already possesses an active on-chain digital twin certificate.")
        return redirect('product_list')

    if request.method == 'POST':
        # Verify that the user has completed the cryptographic signature check
        verified_wallet = request.session.get('verified_wallet_address')
        if not verified_wallet:
            messages.error(request, "Security verification failed: Please verify your MetaMask wallet first.")
            # FIXED: Added correct namespace prefix to redirect route
            return redirect('nft:nft_mint', product_id=product.product_id)

        try:
            token_id = int(request.POST.get('token_id'))
            contract_address = request.POST.get('contract_address')
            ipfs_hash = request.POST.get('ipfs_hash', 'N/A')
            metadata_uri = request.POST.get('metadata_uri', 'N/A')

            NFTService.record_minted_twin({
                'product': product,
                'token_id': token_id,
                'contract_address': contract_address,
                'ipfs_hash': ipfs_hash,
                'metadata_uri': metadata_uri,
                'minted_by': request.user.user_id
            })

            # Clear verified wallet session
            if 'verified_wallet_address' in request.session:
                del request.session['verified_wallet_address']

            messages.success(request, "Product digital twin successfully minted and registered on-chain.")
            # FIXED: Added correct namespace prefix to redirect route
            return redirect('nft:nft_list')
        except Exception as e:
            messages.error(request, f"On-chain minting registration failed: {str(e)}")

    context = {
        'product': product,
        'breadcrumbs': [
            {'title': 'Commodities Registry', 'url': '/products/list/'},
            {'title': 'Initialize On-Chain Twin', 'url': '#'}
        ]
    }
    return render(request, 'nft/nft_mint.html', context)