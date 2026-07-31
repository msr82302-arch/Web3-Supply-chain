from django.db import transaction
from django.utils import timezone
from apps.analytics.models import AIAnalysis, FraudReport, AuditLog

class AnalyticsService:
    @staticmethod
    @transaction.atomic
    def record_ml_evaluation(evaluation_payload) -> AIAnalysis:
        """Securely logs an automated screening execution row."""
        return AIAnalysis.objects.create(created_at=timezone.now(), **evaluation_payload)

    @staticmethod
    @transaction.atomic
    def issue_security_incident(incident_payload) -> FraudReport:
        """Atomically locks an active supply-chain risk case entry into PostgreSQL."""
        return FraudReport.objects.create(
            report_status="OPEN_INVESTIGATION",
            created_at=timezone.now(),
            **incident_payload
        )


class AuditService:
    @staticmethod
    @transaction.atomic
    def commit_audit_trail(audit_payload) -> AuditLog:
        """Writes structural system operation logs natively down to jsonb storage layouts."""
        return AuditLog.objects.create(created_at=timezone.now(), **audit_payload)
