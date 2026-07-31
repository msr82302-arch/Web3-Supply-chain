# apps/dashboard/urls.py
from django.urls import path
from .views import dashboard_home_view

app_name = "dashboard"

urlpatterns = [
    path("", dashboard_home_view, name="home"),
]