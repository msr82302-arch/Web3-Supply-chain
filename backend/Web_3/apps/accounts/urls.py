from django.urls import path
from apps.accounts.views import (
    render_onboarding_view, 
    render_login_view, 
    render_unified_dashboard, 
    inspect_operator_profile, 
    logout_action,
    render_password_reset_view,
    render_password_reset_confirm_view
)

app_name = 'accounts'

urlpatterns = [
    path('register/', render_onboarding_view, name='register'),
    path('login/', render_login_view, name='login'),
    path('logout/', logout_action, name='logout'),
    
    path('forgot-password/', render_password_reset_view, name='forgot_password'),
    path('password-reset/', render_password_reset_view, name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', render_password_reset_confirm_view, name='password_reset_confirm'),
    
    path('dashboard/', render_unified_dashboard, name='dashboard'),
    path('operator/profile/<uuid:operator_uuid>/', inspect_operator_profile, name='operator_profile'),
]