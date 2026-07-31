from django.db import models

# Create your models here.
import uuid


# Direct Python import to establish the product relationship cleanly
from apps.products.models import Product

class AIAnalysis(models.Model):
    # Primary Key
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Key mapping directly back to the physical product evaluated
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='product_id',
        related_name='ai_analyses'
    )
    
    # Loose UUID tracking for the user or system worker triggering the model execution
    analyzed_by = models.UUIDField()
    
    # ML Model Metadata & Prediction Output
    analysis_type = models.CharField(max_length=100)
    prediction = models.TextField()
    
    # Precision Score (numeric(5,2) translates to max_digits=5, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Execution Tracking
    model_name = models.CharField(max_length=150)
    model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."ai_analysis"'
        verbose_name = "AI Analysis"
        verbose_name_plural = "AI Analyses"


class FraudReport(models.Model):
    # Primary Key
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Key to Product
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column='product_id',
        related_name='fraud_reports'
    )
    
    # Loose UUID reference tracking the reporter
    reported_by = models.UUIDField()
    
    # Foreign Key associating this alert to its foundational ML screening model execution
    ai_analysis = models.ForeignKey(
        AIAnalysis,
        on_delete=models.SET_NULL,
        db_column='ai_analysis_id',
        related_name='fraud_reports',
        blank=True,
        null=True
    )
    
    # Risk Metrics & Flags
    fraud_score = models.DecimalField(max_digits=5, decimal_places=2)
    fraud_level = models.CharField(max_length=50)
    report_status = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    
    # Timeline Resolution
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."fraud_reports"'
        verbose_name = "Fraud Report"
        verbose_name_plural = "Fraud Reports"


class AuditLog(models.Model):
    # Primary Key
    audit_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Tracking Actor Context
    user_id = models.UUIDField(blank=True, null=True)
    action = models.CharField(max_length=100)
    
    # System Change Context
    entity_name = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    
    # Data State Diffs (maps perfectly to PostgreSQL jsonb column types)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    # Security Telemetry Network Tracing
    ip_address = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."audit_logs"'
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
