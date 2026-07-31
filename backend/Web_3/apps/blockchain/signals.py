from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from apps.blockchain.models import BlockchainTransaction
from services.email_service import EnterpriseEmailService  # Standard transactional email service interface

@receiver(post_save, sender=BlockchainTransaction)
def trigger_blockchain_event_notifications(sender, instance, created, **kwargs):
    """Listens to verified transactions to dispatch alerts using the shared base email architecture."""
    if not created:
        return
        
    recipient_email = "operator@local.network"  # Platform administration dispatch fallback
    
    if instance.transaction_type == "MINT" and instance.status == "CONFIRMED":
        context = {
            "order_id": str(instance.transaction_id)[:8],
            "buyer_name": "SCM Consortium Minting Node",
            "gross_total": float(instance.gas_fee or 0),
            "items_list": [
                {
                    "product_name": f"ERC-721 Token Minting Proof. Tx Hash: {instance.transaction_hash}",
                    "quantity": 1,
                    "unit_price": float(instance.gas_fee or 0),
                    "subtotal": float(instance.gas_fee or 0)
                }
            ]
        }
        
        try:
            EnterpriseEmailService.dispatch_transactional_template(
                template_name="invoice.html",
                context=context,
                recipient_email=recipient_email,
                subject_line=f"[Consensus] Digital Twin Minted on Network: {instance.network}"
            )
        except Exception:
            pass  # Fail gracefully to avoid blocking database transactions