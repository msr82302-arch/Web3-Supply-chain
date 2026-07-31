from django.urls import path
from apps.sys_setting import views

app_name = 'sys_setting'

urlpatterns = [
    # UI Component Router Links (Loads views asynchronously with HTMX)
    path('', views.settings_dashboard_view, name='settings-dashboard'),
    path('tab/<str:tab_name>/', views.load_settings_tab, name='settings-tab-render'),
    
    # REST API Endpoints matching template actions exactly
    path('api/general/', views.GeneralSettingsAPI.as_view(), name='api-general'),
    path('api/security/', views.SecuritySettingsAPI.as_view(), name='api-security'),
    path('api/notifications/', views.NotificationSettingsAPI.as_view(), name='api-notifications'),
    path('api/blockchain/', views.BlockchainSettingsAPI.as_view(), name='api-blockchain'),
    path('api/api-keys/', views.APISettingsAPI.as_view(), name='api-keys'),
    
    # Visual Email Preview Controllers
    path('test-email/verify/', views.preview_verify_email_template, name='test-email-verify'),
    path('test-email/reset-password/', views.preview_password_reset_template, name='test-email-reset'),
    path('test-email/shipment/', views.preview_shipment_notification_template, name='test-email-shipment'),
    path('test-email/invoice/', views.preview_invoice_template, name='test-email-invoice'),
]