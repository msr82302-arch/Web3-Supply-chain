# apps/orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.orders import views

# Initialize the DRF Default Router
api_router = DefaultRouter()
api_router.register(r'api-orders', views.OrderViewSet, basename='order')

urlpatterns = [
    # 1. Programmatic REST API Gateway Channel
    path('api/', include(api_router.urls)),

    # 2. Secure Server-Rendered HTML Dashboards (DTL)
    path('', views.order_list_html_view, name='order_list'), # FIXED: Direct root mapping for /orders/ and /orders [1]
    path('list/', views.order_list_html_view, name='order_list_legacy'), # Kept for backward compatibility
    path('create/', views.order_create_html_view, name='order_create'),
    path('<uuid:order_id>/detail/', views.order_detail_html_view, name='order_detail'),
    path('<uuid:order_id>/update/', views.order_update_html_view, name='order_update'),
]