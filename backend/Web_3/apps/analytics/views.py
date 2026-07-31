# apps/analytics/views.py
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.analytics.models import AIAnalysis, FraudReport, AuditLog
from apps.analytics.serializer import AIAnalysisSerializer, FraudReportDetailSerializer, FraudReportCreateSerializer, AuditLogSerializer
# FIXED: Changed imports to singular form to match disk filenames
from apps.analytics.service import AnalyticsService, AuditService
from apps.analytics.selector import AnalyticsSelector
from apps.analytics.permission import IsAuditLogAuthorized
from apps.accounts.decorators import restrict_to_roles

class AIAnalysisViewSet(viewsets.ModelViewSet):
    """Processes automated screening records and model telemetry predictions."""
    permission_classes = [IsAuthenticated]
    serializer_class = AIAnalysisSerializer

    def get_queryset(self):
        return AnalyticsSelector.get_visible_analyses(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Enforce user context securely
        validated_data['analyzed_by'] = request.user.user_id
        
        analysis = AnalyticsService.record_ml_evaluation(validated_data)
        return Response(AIAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)


class FraudReportViewSet(viewsets.ModelViewSet):
    """Primary operational interface tracking SCM deviations, duplicate tags, and fraud vectors."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AnalyticsSelector.get_visible_fraud_reports(self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FraudReportDetailSerializer
        return FraudReportCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Enforce user context securely
        validated_data['reported_by'] = request.user.user_id
        
        report = AnalyticsService.issue_security_incident(validated_data)
        return Response(FraudReportDetailSerializer(report).data, status=status.HTTP_201_CREATED)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable platform operations ledger (Read-Only to lock security tracking loops)."""
    permission_classes = [IsAuthenticated, IsAuditLogAuthorized]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        return AnalyticsSelector.get_visible_audit_logs(self.request.user)


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

@login_required
@restrict_to_roles(allowed_roles=['ADMIN', 'ADMINISTRATOR', 'AUDITOR'])
def audit_log_list_html_view(request):
    """Renders active system governance audit trails restricted to administrative roles."""
    logs = AnalyticsSelector.get_visible_audit_logs(request.user).order_by('-created_at')
    metrics = AnalyticsSelector.get_company_ledger_metrics(request.user)
    context = {
        'audit_logs': list(logs),
        'metrics': metrics,
        'breadcrumbs': [{'title': 'Operations Audit Ledger', 'url': '#'}]
    }
    return render(request, 'analytics/analytics_dashboard.html', context)


@login_required
@restrict_to_roles(allowed_roles=['MANUFACTURER', 'ADMIN', 'ADMINISTRATOR', 'AUDITOR'])
def ai_analysis_list_html_view(request):
    """Renders active automated product screening evaluations securely."""
    evaluations = AnalyticsSelector.get_visible_analyses(request.user).order_by('-created_at')
    context = {
        'analysis_list': list(evaluations),
        'breadcrumbs': [
            {'title': 'Operations Audit Ledger', 'url': '/analytics/dashboard/'},
            {'title': 'Cognitive Telemetry Matrix', 'url': '#'}
        ]
    }
    return render(request, 'analytics/insights.html', context)


@login_required
@restrict_to_roles(allowed_roles=['MANUFACTURER', 'ADMIN', 'ADMINISTRATOR', 'AUDITOR'])
def fraud_report_list_html_view(request):
    """Renders supply-chain risk and fraud reports securely."""
    reports = AnalyticsSelector.get_visible_fraud_reports(request.user).order_by('-created_at')
    context = {
        'report_list': list(reports),
        'breadcrumbs': [
            {'title': 'Operations Audit Ledger', 'url': '/analytics/dashboard/'},
            {'title': 'Security Risk Center', 'url': '#'}
        ]
    }
    return render(request, 'analytics/reports.html', context)