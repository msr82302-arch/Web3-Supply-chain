# apps/notifications/views.py
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.notifications.models import Notification
from apps.notifications.serializer import NotificationSerializer
from apps.notifications.service import NotificationService
from apps.notifications.selector import NotificationSelector
from apps.accounts.decorators import restrict_to_roles

class NotificationViewSet(viewsets.ModelViewSet):
    """Primary operational interface delivering alerts, system warnings, and ledger status updates."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # FIXED: Enforced authenticated request user as the authoritative source of identity
        return NotificationSelector.get_user_notifications(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Enforce user context securely
        validated_data['user_id'] = request.user.user_id
        
        alert = NotificationService.dispatch_alert(validated_data)
        return Response(NotificationSerializer(alert).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Custom endpoint allowing frontend clients to clear an operational user's unread list."""
        # FIXED: Resolved user identity directly from request session context
        total_cleared = NotificationService.bulk_mark_as_read(request.user.user_id)
        return Response({"success": True, "message": f"Successfully cleared {total_cleared} unread alerts."}, status=status.HTTP_200_OK)


# =========================================================================
# SERVER SIDE WEB ADMINISTRATIVE HTML DASHBOARD RENDER CHANNELS (DTL)
# =========================================================================

@login_required
def notification_center_view(request):
    """Renders active ecosystem alerts securely scoped to the active user context."""
    # FIXED: Enforced strict user-scoping to prevent cross-tenant data leakage
    alerts = NotificationSelector.get_user_notifications(request.user)
    context = {
        'notifications_list': list(alerts),
        'unread_count': alerts.filter(is_read=False).count(),
        'breadcrumbs': [{'title': 'Notification Center', 'url': '#'}]
    }
    return render(request, 'notifications/notify_center.html', context)


@login_required
def notification_detail_view(request, notification_id):
    """Renders deep detailed verification logs for specific alerts."""
    # FIXED: Enforced strict ownership validation to prevent IDOR access
    visible_alerts = NotificationSelector.get_user_notifications(request.user)
    alert = get_object_or_404(visible_alerts, notification_id=notification_id)
    if not alert.is_read:
        alert.is_read = True
        alert.save()
    context = {
        'alert': alert,
        'breadcrumbs': [
            {'title': 'Notification Center', 'url': '/notifications/center/'},
            {'title': 'Alert Diagnostics Audit', 'url': '#'}
        ]
    }
    return render(request, 'notifications/notify_detail.html', context)


@login_required
@restrict_to_roles(allowed_roles=['ADMIN', 'ADMINISTRATOR', 'AUDITOR'])
def system_alerts_view(request):
    """Renders system infrastructure logs restricted to administrative roles."""
    # FIXED: Enforced company tenant filtering on querysets
    system_errors = NotificationSelector.get_user_notifications(request.user).filter(
        notification_type__in=['DANGER', 'CRITICAL', 'WARNING']
    )
    context = {
        'system_logs': list(system_errors),
        'breadcrumbs': [{'title': 'System Alerts Log', 'url': '#'}]
    }
    return render(request, 'notifications/system_alerts.html', context)


@login_required
@restrict_to_roles(allowed_roles=['LOGISTICS', 'MANUFACTURER', 'ADMIN'])
def activity_feed_view(request):
    """Renders real-time transit Waypoint logs."""
    # FIXED: Enforced company tenant filtering on querysets
    feed = NotificationSelector.get_user_notifications(request.user).filter(notification_type='INFO')
    context = {
        'activity_feed': list(feed),
        'breadcrumbs': [{'title': 'Operations Activity Feed', 'url': '#'}]
    }
    return render(request, 'notifications/activity_feed.html', context)


@login_required
def announcement_list_view(request):
    """Fetches global broadcast messages marked as announcements."""
    # FIXED: Enforced company tenant filtering on querysets
    announcements = NotificationSelector.get_user_notifications(request.user).filter(notification_type='ANNOUNCEMENT')
    context = {
        'announcements': list(announcements),
        'breadcrumbs': [{'title': 'Consortium Announcements', 'url': '#'}]
    }
    return render(request, 'notifications/announce_list.html', context)


@login_required
def account_notify_list_view(request):
    """Provides a minimal, alternative grid index tracking general user alert lines."""
    # FIXED: Enforced company tenant filtering on querysets
    personal_alerts = NotificationSelector.get_user_notifications(request.user)
    context = {
        'personal_alerts': list(personal_alerts),
        'breadcrumbs': [{'title': 'Alerts Index Directory', 'url': '#'}]
    }
    return render(request, 'notifications/notify_list.html', context)


@login_required
def notification_preferences_view(request):
    """Renders control settings to configure decentralized notification dispatch channels."""
    if request.method == 'POST':
        messages.success(request, "Ecosystem dispatch channel preferences saved.")
        return redirect('notification_list')
        
    context = {
        'breadcrumbs': [{'title': 'Dispatch Settings Matrix', 'url': '#'}]
    }
    return render(request, 'notifications/notify_preferences.html', context)