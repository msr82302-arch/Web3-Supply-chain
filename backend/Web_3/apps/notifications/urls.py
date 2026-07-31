# apps/notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.notifications import views

# Initialize the DRF Default Router
api_router = DefaultRouter()
api_router.register(r'alerts', views.NotificationViewSet, basename='notification-alert')

urlpatterns = [
    # 1. Programmatic REST API Gateway Channel
    path('api/', include(api_router.urls)),

    # 2. Secure Server-Rendered HTML Dashboards (DTL)
    path('', views.notification_center_view, name='notification_list'),
    path('<uuid:notification_id>/detail/', views.notification_detail_view, name='notification_detail'),
    path('system-logs/', views.system_alerts_view, name='system_alerts'),
    path('activity/', views.activity_feed_view, name='activity_feed'),
    path('announcements/', views.announcement_list_view, name='announcement_list'),
    path('index/', views.account_notify_list_view, name='account_notify_list'),
    path('preferences/', views.notification_preferences_view, name='notification_preferences'),
]