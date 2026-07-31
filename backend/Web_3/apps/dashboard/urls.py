from django.urls import path
from .views import dashboard_home_view

app_name = 'dashboard'  # Declares explicit app namespace [2]

urlpatterns = [
    path('', dashboard_home_view, name='home'),
]