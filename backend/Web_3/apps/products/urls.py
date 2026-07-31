# apps/products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products import views

# Initialize the DRF Default Router for API endpoints
api_router = DefaultRouter()
api_router.register(r'products', views.ProductViewSet, basename='product')
api_router.register(r'companies', views.CompanyDropdownViewSet, basename='company')
api_router.register(r'categories', views.ProductCategoryViewSet, basename='product-category')

# FIXED: Removed 'app_name = "products"' to register views in the global URL namespace,
# aligning with DTL templates and automated tests.

urlpatterns = [
    # 1. Programmatic REST API Gateway (e.g., /products/api/products/)
    path('api/', include(api_router.urls)),

    # 2. Secure Server-Rendered HTML Dashboards (DTL)
    path('', views.product_list_html_view, name='product_list'),
    path('create/', views.product_create_html_view, name='product_create'),
    path('<uuid:product_id>/detail/', views.product_detail_html_view, name='product_detail'),
    path('<uuid:product_id>/update/', views.product_update_html_view, name='product_update'),
]