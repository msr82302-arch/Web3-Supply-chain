# apps/analytics/serializers.py
from rest_framework import serializers
from apps.analytics.models import AIAnalysis, FraudReport, AuditLog

class AIAnalysisSerializer(serializers.ModelSerializer):
    confidence_score = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = AIAnalysis
        fields = ['analysis_id', 'product', 'analyzed_by', 'analysis_type', 'prediction', 'confidence_score', 'model_name', 'model_version', 'created_at']


class FraudReportDetailSerializer(serializers.ModelSerializer):
    """Provides granular, high-fidelity security risk briefings including underlying AI analysis models."""
    ai_analysis = AIAnalysisSerializer(read_only=True)
    fraud_score = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = FraudReport
        fields = ['report_id', 'product', 'reported_by', 'ai_analysis', 'fraud_score', 'fraud_level', 'report_status', 'description', 'created_at', 'resolved_at']


class FraudReportCreateSerializer(serializers.ModelSerializer):
    fraud_score = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = FraudReport
        fields = ['report_id', 'product', 'reported_by', 'ai_analysis', 'fraud_score', 'fraud_level', 'report_status', 'description', 'resolved_at']


class AuditLogSerializer(serializers.ModelSerializer):
    # Native jsonb structure handling for delta state diff auditing
    old_values = serializers.JSONField(required=False, allow_null=True)
    new_values = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = AuditLog
        fields = ['audit_log_id', 'user_id', 'action', 'entity_name', 'entity_id', 'old_values', 'new_values', 'ip_address', 'user_agent', 'created_at']