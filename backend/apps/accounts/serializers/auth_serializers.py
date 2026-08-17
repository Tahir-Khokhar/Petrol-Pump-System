from django.contrib.auth import authenticate
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import User


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with email and password."""

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                               username=email, password=password)

            if not user:
                raise exceptions.AuthenticationFailed(
                    'Invalid email or password. Please try again.',
                    code='authentication_failed',
                )

            if not user.is_active:
                raise exceptions.AuthenticationFailed(
                    'This account has been deactivated. Please contact an administrator.',
                    code='account_disabled',
                )

            if not user.is_verified and user.role != User.Role.SUPER_ADMIN:
                raise exceptions.AuthenticationFailed(
                    'This account has not been verified yet.',
                    code='account_not_verified',
                )

            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization_required',
            )

        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that adds user info to the token payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for admin to create users."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Minimum 8 characters with at least one letter and one number.',
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password', 'role', 'phone']

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'A user with this email already exists.',
                code='unique',
            )
        return email

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'Password must be at least 8 characters long.',
                code='min_length',
            )
        if not any(c.isalpha() for c in value):
            raise serializers.ValidationError(
                'Password must contain at least one letter.',
                code='invalid_password',
            )
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                'Password must contain at least one number.',
                code='invalid_password',
            )
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'},
                code='password_mismatch',
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_verified = True
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing the authenticated user's password."""

    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Current password is incorrect.',
                code='invalid_password',
            )
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'Password must be at least 8 characters long.',
                code='min_length',
            )
        if not any(c.isalpha() for c in value):
            raise serializers.ValidationError(
                'Password must contain at least one letter.',
                code='invalid_password',
            )
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                'Password must contain at least one number.',
                code='invalid_password',
            )
        return value

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_new_password'):
            raise serializers.ValidationError(
                {'confirm_new_password': 'New passwords do not match.'},
                code='password_mismatch',
            )
        if attrs.get('old_password') == attrs.get('new_password'):
            raise serializers.ValidationError(
                {'new_password': 'New password must be different from the current password.'},
                code='invalid_password',
            )
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for listing and retrieving users (excludes sensitive fields)."""

    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'is_active', 'is_verified',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'email', 'role', 'is_verified', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the authenticated user's own profile endpoint."""

    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'is_active', 'is_verified',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'uuid', 'email', 'role', 'role_display',
            'is_active', 'is_verified', 'created_at', 'updated_at',
        ]

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""

    full_name = serializers.SerializerMethodField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'full_name', 'role_display', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()
