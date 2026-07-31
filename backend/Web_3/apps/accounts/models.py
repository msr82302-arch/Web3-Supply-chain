# apps/accounts/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class EnterpriseUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email: 
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        
        # During admin generation, ensure the default role mapping exists cleanly
        if 'role' not in extra_fields:
            try:
                role = Role.objects.filter(role_name__in=['ADMIN', 'ADMINISTRATOR', 'Manufacturer']).first()
                if not role:
                    role = Role.objects.create(role_name='ADMIN', description='Default administrator role')
                extra_fields['role'] = role
            except Exception:
                pass
                
        return self.create_user(email, password, **extra_fields)


class Company(models.Model):
    company_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=100, unique=True)
    tax_number = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'companies'

    def __str__(self):
        return self.company_name


class Role(models.Model):
    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_name = models.CharField(max_length=50, unique=True) # MANUFACTURER, LOGISTICS, BUYER, AUDITOR
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return self.role_name


class User(AbstractBaseUser):
    """Primary system operator transaction node matching absolute unmanaged parameters."""
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        db_column='company_id',
        related_name='users',
        null=True,
        blank=True
    )
    
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        db_column="role_id", 
        related_name="users"
    )
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    
    # Matches exact password hash column
    password = models.CharField(max_length=255, db_column="password_hash")
    
    phone = models.CharField(max_length=30, null=True, blank=True)
    profile_image = models.TextField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    is_staff = models.BooleanField(default=False)
    
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EnterpriseUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        managed = False
        db_table = 'users'

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff