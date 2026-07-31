# apps/accounts/serializers.py
from rest_framework import serializers
from apps.accounts.models import User, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'role_name', 'description', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """Provides structured user profile outputs along with nested security role data."""
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'user_id', 'email', 'first_name', 
            'last_name', 'role', 'is_active', 'created_at', 'updated_at'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Validates user account initialization parameters against unmanaged columns."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['user_id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'password']

    def validate_email(self, value):
        """Business check ensuring platform account email strings remain unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An operational user account with this email address already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user