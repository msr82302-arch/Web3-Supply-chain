# apps/nft/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.nft import views

app_name = 'nft'

# Initialize the DRF Default Router
api_router = DefaultRouter()
api_router.register(r'tokens', views.NFTViewSet, basename='nft-token')
api_router.register(r'ownership', views.OwnershipHistoryViewSet, basename='ownership-history')

urlpatterns = [
    # 1. Programmatic REST API Gateway Channel
    path('api/', include(api_router.urls)),

    # 2. Cryptographic signature verification endpoints
    path('wallet/challenge/', views.wallet_challenge_api, name='wallet_challenge_api'),
    path('wallet/verify/', views.wallet_verify_api, name='wallet_verify_api'),

    # 3. Secure Server-Rendered HTML Dashboards (DTL)
    path('', views.nft_list_html_view, name='nft_list'),
    path('<uuid:nft_id>/', views.nft_detail_html_view, name='nft_detail'),
    path('mint/<uuid:product_id>/', views.nft_mint_html_view, name='nft_mint'),
   
]