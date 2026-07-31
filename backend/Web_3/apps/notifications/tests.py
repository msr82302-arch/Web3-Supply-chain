# apps/notifications/tests.py
import uuid
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.notifications.models import Notification
from apps.notifications.service import NotificationService

User = get_user_model()

@override_settings(MIGRATION_MODULES={
    'accounts': None,
    'companies': None,
    'products': None,
    'nft': None,
    'orders': None,
    'shipments': None,
    'notifications': None,
})
class NotificationsStabilizationTests(TestCase):
    def setUp(self):
        # Dynamically set managed=True for tests so that tables are generated in SQLite
        Notification._meta.managed = True

        self.user_a = User.objects.create_user(
            email="usera@scm.com",
            password="securepassword123",
            first_name="User",
            last_name="A"
        )
        self.user_b = User.objects.create_user(
            email="userb@scm.com",
            password="securepassword123",
            first_name="User",
            last_name="B"
        )

        self.client = Client()

    def test_notification_creation_via_service(self):
        alert = NotificationService.dispatch_alert({
            'user_id': self.user_a.user_id,
            'title': "Transaction Confirmation",
            'message': "Consensus on-chain signature recorded.",
            'notification_type': "INFO"
        })
        self.assertEqual(alert.title, "Transaction Confirmation")
        self.assertFalse(alert.is_read)

    def test_tenant_user_isolation_restriction(self):
        # Create notification for User A
        alert = Notification.objects.create(
            user_id=self.user_a.user_id,
            title="Private Alert",
            message="Secret parameters parsed.",
            notification_type="WARNING"
        )

        # Log in as User B
        self.client.login(username="userb@scm.com", password="securepassword123")
        
        # Accessing detail view of User A's alert must return 404
        url = reverse('notification_detail', kwargs={'notification_id': alert.notification_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404) # Enforces strict IDOR protection

    def test_unauthenticated_user_view_redirects_to_login(self):
        url = reverse('notification_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirects to login