from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.companies import views

# Isolate the DRF API engine away from standard browser routing paths
api_router = DefaultRouter()
api_router.register(r'profiles', views.CompanyViewSet, basename='api-company')

urlpatterns = [
    # API Gateway Namespace
    path('api/', include(api_router.urls)),

    # Secure Server-Rendered HTML Dashboards
    path('', views.company_list_html_view, name='company_list'),
    path('create/', views.company_create_html_view, name='company_create'),
    
    
    
    
    
    path('<uuid:company_id>/', views.company_detail_html_view, name='company_detail'),
    path('<uuid:company_id>/update/', views.company_update_html_view, name='company_update'),
]
