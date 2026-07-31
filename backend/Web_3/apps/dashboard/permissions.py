# apps/accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid

# ==============================================================================
# 1. DATABASE MANAGER LAYER
# ==============================================================================
class UnmanagedUserManager(BaseUserManager):
    """Custom manager handling creation overrides for unmanaged table layers."""
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, username, password, **extra_fields)


# ==============================================================================
# 2. ROLE MODEL (Defined first so User model can reference it below)
# ==============================================================================
class Role(models.Model):
    """Administrative access node defining clearance tiers and profiles."""
    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return self.role_name


# ==============================================================================
# 3. USER MODEL
# ==============================================================================
class User(AbstractBaseUser):
    """Primary system operator transaction node matching unmanaged schema layout."""
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(null=True, blank=True)
    
    # Safe reference now that Role is declared above
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        db_column="role_id", 
        related_name="users"
    )
    
    username = models.CharField(max_length=255, unique=True)
    email = models.CharField(max_length=255, unique=True)
    password = models.TextField(db_column="password_hash") 
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, null=True, blank=True)
    profile_image = models.TextField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UnmanagedUserManager()

    # Core configuration links for Django Auth engine processing
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
