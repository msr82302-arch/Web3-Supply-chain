import uuid
import logging
from django.db import transaction, connection
from django.utils import timezone
from apps.blockchain.models import Wallet, BlockchainTransaction, OwnershipHistory

logger = logging.getLogger(__name__)

def is_valid_uuid(val):
    """Utility function to safely check if a value is a valid UUID string format."""
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

class BlockchainService:
    """Central Web3 consensus and data serialization service engine."""

    @staticmethod
    @transaction.atomic
    def generate_auth_challenge(session) -> str:
        """Generates a secure cryptographic challenge and binds it to the user session."""
        challenge_nonce = f"Sign this cryptographic message to authenticate your wallet. Nonce: {uuid.uuid4().hex}"
        session['wallet_auth_challenge'] = challenge_nonce
        session.modified = True
        return challenge_nonce

    @staticmethod
    @transaction.atomic
    def verify_wallet_signature(session, wallet_address, signature_hex) -> bool:
        """Verifies an EIP-191 personal_sign cryptographic signature against the session challenge."""
        challenge_text = session.get('wallet_auth_challenge')
        if not challenge_text or not wallet_address or not signature_hex:
            return False

        try:
            from web3 import Web3
            from eth_account.messages import encode_defunct
            
            w3 = Web3()
            message = encode_defunct(text=challenge_text)
            recovered_addr = w3.eth.account.recover_message(message, signature=signature_hex)
            
            # Enforce clean lowercase address comparison
            if recovered_addr.lower() == wallet_address.lower():
                # Invalidate nonce to prevent replay attacks
                session['wallet_auth_challenge'] = None
                session.modified = True
                return True
        except Exception as e:
            logger.error(f"[VERIFY_SIGNATURE_ERROR] Signature recovery failed: {str(e)}")
        
        return False

    @staticmethod
    @transaction.atomic
    def register_verified_wallet(user_id, wallet_payload) -> Wallet:
        """Saves a cryptographically verified wallet structure to PostgreSQL."""
        # Clean inputs before writing
        user_uuid = user_id if is_valid_uuid(user_id) else uuid.uuid4()
        return Wallet.objects.create(
            wallet_id=uuid.uuid4(),
            user_id=user_uuid,
            is_verified=True,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            **wallet_payload
        )

    @staticmethod
    @transaction.atomic
    def log_onchain_transaction(tx_payload) -> BlockchainTransaction:
        """Logs an on-chain ledger audit log row into PostgreSQL with transaction idempotency protection."""
        tx_hash = tx_payload.get('transaction_hash')
        
        # Idempotency Protection: Prevent duplicate entries
        existing_tx = BlockchainTransaction.objects.filter(transaction_hash=tx_hash).first()
        if existing_tx:
            return existing_tx

        return BlockchainTransaction.objects.create(
            transaction_id=uuid.uuid4(),
            status=tx_payload.get('status', 'CONFIRMED'),
            created_at=timezone.now(),
            **tx_payload
        )

    @staticmethod
    @transaction.atomic
    def commit_custody_transfer(product, previous_owner, current_owner, tx_hash=None, remarks="") -> OwnershipHistory:
        """Commits product ownership transitions, optionally linking to a verified blockchain transaction."""
        blockchain_tx = None
        if tx_hash:
            blockchain_tx = BlockchainTransaction.objects.filter(transaction_hash=tx_hash).first()
            if not blockchain_tx:
                # Fallback to create transactional record log
                blockchain_tx = BlockchainTransaction.objects.create(
                    transaction_id=uuid.uuid4(),
                    transaction_hash=tx_hash,
                    block_number=0,
                    network="Ethereum",
                    gas_fee=0,
                    transaction_type="TRANSFER",
                    status="CONFIRMED",
                    created_at=timezone.now()
                )

        return OwnershipHistory.objects.create(
            ownership_id=uuid.uuid4(),
            product=product,
            previous_owner=previous_owner if is_valid_uuid(previous_owner) else None,
            current_owner=current_owner,
            blockchain_transaction=blockchain_tx,
            transfer_date=timezone.now(),
            remarks=remarks
        )