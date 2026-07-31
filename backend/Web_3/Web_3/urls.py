# backend/Web_3/Web_3/urls.py










'''
URL configuration for Web_3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

'''

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

# Change render_registration_view to render_onboarding_view
from apps.accounts.views import render_onboarding_view 

from apps.orders import views
from apps.shipments import views
from apps.verification import views
from apps.blockchain import views
from apps.dashboard import views



from apps.companies.views import (
    company_list_html_view,
    company_detail_html_view,
    company_update_html_view,
    company_create_html_view
)



from apps.products import views
from apps.nft import views
from apps.notifications import views

from apps.analytics import views
from apps.sys_setting import views




 



urlpatterns = [
    path(" ", include("apps.dashboard.urls")),
    # ----------------------------------------------------
    # 1. CORE BACKEND REST API CHANNELS (DO NOT MODIFY)
    # ----------------------------------------------------
    path("admin/", admin.site.urls),
    path("products/", include("apps.products.urls")),
    
    path("companies/", include("apps.companies.urls")),
    path("orders/", include("apps.orders.urls")),
    path("shipments/", include("apps.shipments.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("verification/", include("apps.verification.urls")),
    
    path("nft/", include("apps.nft.urls")),
    path("setting/", include("apps.sys_setting.urls")),


    # 3. Headless React Frontend Core REST API Gateway Network Channel
    # Maps REST requests to DRF ViewSets (e.g., /api/companies/profiles/)
    path('api/companies/', include('apps.companies.urls')),
    
    path("accounts/", include("apps.accounts.urls")),
    path("blockchain/",include("apps.blockchain.urls")),


   
    
    # ----------------------------------------------------
    # 2. REAL DASHBOARD PRODUCTION TEST ROUTE
    # ----------------------------------------------------
    path('test-components/', TemplateView.as_view(
        template_name='dashboard.html',
        extra_context={
            'breadcrumbs': [
                {'title': 'Operations Terminal Console', 'url': '#'},
                {'title': 'Ecosystem Overview Workspace', 'url': '#'}
            ],
            # Live Mock Data to feed Section 3 & 4 Tables
            'recent_shipments': [
                {'id': '10824', 'reference_id': '0x9a8b7c6d', 'cargo_title': 'Polypropylene Resins Batch A-90', 'telemetry_temp': '3.8', 'critical_flag': False},
                {'id': '10823', 'reference_id': '0x4e5f6a7b', 'cargo_title': 'Serialized Medical Vials Type-IV', 'telemetry_temp': '5.4', 'critical_flag': True},
                {'id': '10822', 'reference_id': '0x1c2d3e4f', 'cargo_title': 'Structural Aerospace Grade Aluminum', 'telemetry_temp': '14.2', 'critical_flag': False}
            ],
            'recent_products': [
                {'sku': 'GTIN-90812401', 'gtin_code': '109081240192', 'title': 'High Density Polyethylene Pellets', 'total_units': '14,800'},
                {'sku': 'GTIN-87239105', 'gtin_code': '508723910521', 'title': 'Cold-Chain Insulin Storage Packs', 'total_units': '2,450'},
                {'sku': 'GTIN-65120492', 'gtin_code': '706512049283', 'title': 'Tempered Structural Carbon Fiber Threads', 'total_units': '6,100'}
            ],
            'recent_blocks': [
                {'id': '395021', 'number': '395021', 'hash': '0x7a8b9c2d1e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b', 'validator': 'AWS-Virginia-Node-01'},
                {'id': '395020', 'number': '395020', 'hash': '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', 'validator': 'GCP-Frankfurt-Node-04'},
                {'id': '395018', 'number': '395019', 'hash': '0xf8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2b1a0f9e8d7', 'validator': 'Azure-Tokyo-Node-02'}
            ]
        }
    ), name='test_all_components'),

    # ----------------------------------------------------
    # 3. ACCOUNTS SUBSYSTEM TEST VIEWS
    
    
    #accounts paths
    
    #layouts path
    path('test-auth/', TemplateView.as_view(template_name='layouts/auth_layout.html'), name='test_auth_layout'),
    path('test-dashboard/', TemplateView.as_view(template_name='layouts/dashboard.html'), name='test_dashboard_layout'),
        # Open backend/Web_3/Web_3/urls.py
    # TEMPORARY COMPANIES SUBSYSTEM TESTING ENDPOINTS
    
        # ----------------------------------------------------
    # 4. COMPANIES SUBSYSTEM DYNAMIC PRODUCTION ROUTING
    # ----------------------------------------------------
    
   
    #for orders 
   
    #shipments apps
    
   

    


    
]

    

