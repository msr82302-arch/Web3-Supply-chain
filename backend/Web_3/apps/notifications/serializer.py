# apps/notifications/serializers.py
from rest_framework import serializers
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['notification_id', 'user_id', 'title', 'message', 'notification_type', 'is_read', 'created_at']
        read_only_fields = ['notification_id', 'user_id', 'is_read', 'created_at']