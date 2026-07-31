# apps/verification/services.py
import hmac
import hashlib
import time
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.verification.models import QRCode, VerificationLog
from apps.analytics.service import AnalyticsService

class VerificationService:
    @staticmethod
    @transaction.atomic
    def issue_qr_label(label_data) -> QRCode:
        """Securely creates a product scannable entry profile."""
        return QRCode.objects.create(**label_data)

    @staticmethod
    @transaction.atomic
    def log_scan_event(qr: QRCode, scan_metadata) -> VerificationLog:
        """Atomically appends an audit scan event tracking transaction to PostgreSQL."""
        return VerificationLog.objects.create(qr=qr, **scan_metadata)

    @staticmethod
    def generate_dynamic_signature(qr_id: str, timestamp: int) -> str:
        """Generates a cryptographically secure HMAC-SHA256 signature [1]."""
        secret_key = settings.SECRET_KEY.encode()
        message = f"{qr_id}_{timestamp}".encode()
        return hmac.new(secret_key, message, hashlib.sha256).hexdigest()

    @staticmethod
    @transaction.atomic
    def verify_dynamic_qr_code(qr: QRCode, signature: str, timestamp_str: str, scan_metadata: dict) -> VerificationLog:
        """
        Validates the time-based cryptographic signature of a scanned QR code [1].
        If invalid or expired (older than 1 hour), it flags the transaction as fraud [1].
        """
        is_authentic = True
        reason = "SUCCESS"

        try:
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            
            # 1. Check expiration threshold (e.g. 1 hour / 3600 seconds)
            if abs(current_time - timestamp) > 3600:
                is_authentic = False
                reason = "EXPIRED_SIGNATURE"
                
            # 2. Recalculate and verify signature
            expected_sig = VerificationService.generate_dynamic_signature(str(qr.qr_id), timestamp)
            if not hmac.compare_digest(expected_sig, signature):
                is_authentic = False
                reason = "FRAUD_SUSPECTED"
                
        except (ValueError, TypeError):
            is_authentic = False
            reason = "MALFORMED_PARAMETERS"

        scan_metadata['verification_result'] = reason

        # Log the verification event
        log_entry = VerificationService.log_scan_event(qr, scan_metadata)

        # Trigger security alerts if fraud is detected
        if not is_authentic:
            try:
                AnalyticsService.issue_security_incident({
                    'product': qr.product,
                    'reported_by': scan_metadata.get('verified_by') or qr.product.manufacturer_company_id,
                    'fraud_score': 99.00 if reason == "FRAUD_SUSPECTED" else 50.00,
                    'fraud_level': "CRITICAL" if reason == "FRAUD_SUSPECTED" else "HIGH",
                    'description': f"SCM Security Guard: Counterfeit scan detected. Code: {reason}. IP: {scan_metadata.get('ip_address')}."
                })
            except Exception:
                pass # Non-blocking security triggers

        return log_entry