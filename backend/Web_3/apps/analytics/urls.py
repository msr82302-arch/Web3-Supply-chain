# apps/analytics/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.analytics import views

# FIXED: Registered local application namespace to align with templates and test selectors
app_name = 'analytics'

# Initialize the DRF Default Router
api_router = DefaultRouter()
api_router.register(r'ai-evaluations', views.AIAnalysisViewSet, basename='ai-analysis')
api_router.register(r'fraud-alerts', views.FraudReportViewSet, basename='fraud-report')
api_router.register(r'audit-trails', views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # 1. Programmatic REST API Gateway Channel
    path('api/', include(api_router.urls)),

    # 2. Secure Server-Rendered HTML Dashboards (DTL)
    path('dashboard/', views.audit_log_list_html_view, name='analytics_dashboard'),
    path('insights/', views.ai_analysis_list_html_view, name='analytics_insights'),
    path('reports/', views.fraud_report_list_html_view, name='analytics_reports'),
]