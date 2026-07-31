from django.urls import path
from apps.blockchain import views

app_name = 'blockchain'

urlpatterns = [
    # Interactive Console HTML Views [2]
    path('', views.wallet_list_html_view, name='wallet-list'),
    path('wallets/', views.wallet_list_html_view, name='wallet-list-explicit'),  # Resolves the /blockchain/wallets/ 404 [2]
    path('wallets-alt/', views.wallet_list_html_view, name='wallet_list'),       # Underscore alias [2]
    
    path('transactions/', views.transaction_history_html_view, name='transaction-list'),
    path('transactions-alt/', views.transaction_history_html_view, name='transaction_list'), # Underscore alias [2]
    
    path('ownership/', views.ownership_history_html_view, name='ownership-history'),
    path('ownership-alt/', views.ownership_history_html_view, name='ownership_history'), # Underscore alias [2]
    
    path('nft-hub/', views.nft_hub_html_view, name='nft-hub'),
    path('nft_hub/', views.nft_hub_html_view, name='nft_hub'), # Underscore alias [2]
    
    # REST API & Challenge Endpoints
    path('api/wallets/challenge/', views.WalletChallengeAPI.as_view(), name='api-wallet-challenge'),
    path('api/wallets/verify/', views.WalletVerifyAPI.as_view(), name='api-wallet-verify'),
]