from django.db import models

# Create your models here.
import uuid


class Notification(models.Model):
    # Primary Key
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Loose UUID reference tracking the recipient user
    user_id = models.UUIDField()
    
    # Notification Payload Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50) # Handled character varying format
    
    # State and Delivery Management
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"supply_chain_schema"."notifications"'
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
