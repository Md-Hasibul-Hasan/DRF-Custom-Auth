from .models import *
from rest_framework import serializers
from .utils import Util


from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'password2']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long")
        return value.strip()

    def validate_email(self, value):
        return value.lower()

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        return value

    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2')
        if password != password2:
            raise serializers.ValidationError('Passwords do not match')
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    


class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        return value.lower()




class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'image',
            'is_active'
        ]




class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'image']

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Name must be at least 2 characters long"
            )
        return value.strip()

    def validate_image(self, value):
        max_size = 2 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "Image size must be below 2MB"
            )

        return value




class UserChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )
    new_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )
    confirm_password = serializers.CharField(
        max_length=255, style={'input_type': 'password'}, write_only=True
    )

    class Meta:
        fields = ['current_password', 'new_password', 'confirm_password']

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError('Password must contain at least one digit')
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError('Password must contain at least one uppercase letter')
        return value

    def validate(self, data):
        user = self.context['user']

        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not user.check_password(current_password):
            raise serializers.ValidationError({
                'current_password': 'Current password is not correct'
            })

        if new_password != confirm_password:
            raise serializers.ValidationError('Passwords do not match')

        return data

    def save(self, **kwargs):
        user = self.context['user']
        password = self.validated_data.get('new_password')
        user.set_password(password)
        user.save()
        return user




class SendResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, data):
        email = data.get('email')
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('User does not exist')
        return data




class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, data):
        email = data.get('email')
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('User does not exist')
        user = User.objects.get(email=email)
        if user.is_active:
            raise serializers.ValidationError('Account already verified')
        return data




class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255, style={'input_type': 'password'}, write_only=True)
    confirm_password = serializers.CharField(max_length=255, style={'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password']

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError('Password must contain at least one digit')
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError('Password must contain at least one uppercase letter')
        return value

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError('Passwords do not match')
        return data




class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    otp = serializers.CharField(max_length=6, min_length=6)

    class Meta:
        fields = ['email', 'otp']

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('User does not exist')
        return value.lower()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must contain only digits')
        return value




class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=255, write_only=True)

    def validate_new_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered')
        return value

    def validate(self, data):
        user = self.context['user']
        password = data.get('password')
        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'Password is incorrect'})
        return data

    def save(self, **kwargs):
        user = self.context['user']
        new_email = self.validated_data.get('new_email')
        user.generate_pending_email_otp(new_email)
        return user



class ConfirmChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(max_length=255)
    otp = serializers.CharField(max_length=6, min_length=6, write_only=True)

    def validate_new_email(self, value):
        value = value.lower()
        user = self.context['user']
        if not user.pending_email:
            raise serializers.ValidationError('No pending email change request found')
        if value != user.pending_email:
            raise serializers.ValidationError('New email does not match pending email change request')
        return value

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must contain only digits')
        return value

    def validate(self, data):
        user = self.context['user']
        if not user.verify_pending_email_otp(data.get('otp')):
            raise serializers.ValidationError('Invalid or expired OTP')
        return data

    def save(self, **kwargs):
        user = self.context['user']
        user.email = user.pending_email
        user.pending_email = None
        user.pending_email_otp = None
        user.pending_email_otp_created_at = None
        user.pending_email_otp_expires_at = None
        user.save()
        return user




# 2FA Serializers
class Setup2FASerializer(serializers.Serializer):
    """Serializer for setting up 2FA"""
    method = serializers.ChoiceField(choices=['email'])
    
    def validate(self, data):
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError('User not found in context')
        if user.is_2fa_enabled:
            raise serializers.ValidationError('2FA is already enabled for this user')
        return data




class Enable2FASerializer(serializers.Serializer):
    """Serializer for enabling 2FA after verification"""
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must contain only digits')
        return value
    
    def validate(self, data):
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError('User not found in context')
        
        otp = data.get('otp')
        if not user.two_fa_otp:
            raise serializers.ValidationError('No pending 2FA setup. Please setup 2FA first.')
        
        if not user.verify_2fa_otp(otp):
            raise serializers.ValidationError('Invalid or expired OTP')
        
        return data




class Verify2FASerializer(serializers.Serializer):
    """Serializer for verifying 2FA during login"""
    temp_token = serializers.CharField(write_only=True)
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must contain only digits')
        return value




class Disable2FASerializer(serializers.Serializer):
    """Serializer for disabling 2FA"""
    password = serializers.CharField(max_length=255, write_only=True)
    
    def validate(self, data):
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError('User not found in context')
        
        password = data.get('password')
    
        
        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'Password is incorrect'})
        
        if not user.is_2fa_enabled:
            raise serializers.ValidationError('2FA is not enabled for this user')
        
        # Verify current 2FA OTP for security
        if user.is_2fa_locked():
            raise serializers.ValidationError('2FA is temporarily locked due to too many failed attempts')
        
        return data




class UserSessionSerializer(serializers.ModelSerializer):

    this_device = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id',
            'ip_address',
            'user_agent',
            'created_at',
            'last_activity',
            'is_active',
            'this_device',
        ]

    def get_this_device(self, obj):

        current_jti = self.context.get('current_jti')

        return obj.session_jti == current_jti












