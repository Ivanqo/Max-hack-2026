from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with full details."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'university', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with validation."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )
    role = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'first_name',
            'last_name', 'role', 'university'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        """Validate that email is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Public self-registration must never grant privileged roles.
        requested_role = attrs.get('role', 'student')
        if requested_role != 'student':
            raise serializers.ValidationError({
                "role": "Public registration only supports student accounts."
            })

        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('password2')
        password = validated_data.pop('password')
        validated_data.pop('role', None)
        validated_data['role'] = 'student'
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'university']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'university': {'required': False},
        }

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change with validation."""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        label='Confirm New Password'
    )

    def validate_old_password(self, value):
        """Validate that old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate that new passwords match and differ from old password."""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})

        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from old password."}
            )

        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that includes user data."""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom claims
        data['user'] = UserSerializer(self.user).data

        return data


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout with refresh token."""
    refresh_token = serializers.CharField(required=True)

    def validate_refresh_token(self, value):
        """Validate that refresh token is provided."""
        if not value:
            raise serializers.ValidationError("Refresh token is required.")
        return value
