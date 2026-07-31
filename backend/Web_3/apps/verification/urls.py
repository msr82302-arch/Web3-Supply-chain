# apps/verification/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.verification import views

# FIXED: Registered local application namespace to align with templates and test selectors
app_name = 'verification'

# Initialize the DRF Default Router
api_router = DefaultRouter()
api_router.register(r'qr-codes', views.QRCodeViewSet, basename='qr-code')

urlpatterns = [
    # 1. Programmatic REST API Gateway Channel
    path('api/', include(api_router.urls)),

    # 2. Public Facing Branded consumer verification scan endpoint
    path('verify/<uuid:qr_id>/', views.public_verification_html_view, name='public_verify'),

    # 3. Secure Server-Rendered HTML Dashboards (DTL)
    path('logs/', views.verification_dashboard_html_view, name='verify_dashboard'),
]