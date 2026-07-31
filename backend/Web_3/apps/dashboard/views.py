# apps/dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.dashboard.services import DashboardBusinessService

@login_required(login_url='accounts:login')
def dashboard_home_view(request):
    """
    Renders the unified enterprise dashboard view.
    Orchestrates live telemetry context compiled by the service layer.
    """
    context_payload = DashboardBusinessService.compile_control_center_matrices(request)
    return render(request, "dashboard/dashboard.html", context_payload)