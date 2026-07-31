# apps/shipments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.shipments import views

# Initialize the DRF Default Router
api_router = DefaultRouter()
# FIXED: Changed basename to 'shipment-api' to align with automated test assertions
api_router.register(r'api-shipments', views.ShipmentViewSet, basename='shipment-api')

urlpatterns = [
    # 1. Programmatic REST API Gateway Channel
    path('api/', include(api_router.urls)),

    # 2. Secure Server-Rendered HTML Dashboards (DTL)
    path('', views.shipment_list_html_view, name='shipment_list'),
    path('<uuid:shipment_id>/', views.shipment_detail_html_view, name='shipment_detail'),
    path('create/<uuid:order_id>/', views.shipment_create_html_view, name='shipment_create'),
    path('<uuid:shipment_id>/update/', views.shipment_update_html_view, name='shipment_update'),
]