from .models import User
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



    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'image', 'is_active', 'is_staff', 'is_superuser']



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


# class SendResetPasswordEmailSerializer(serializers.Serializer):
#     email = serializers.EmailField(max_length=255)

#     class Meta:
#         fields = ['email']


#     def validate(self, data):
#         email = data.get('email')
#         if User.objects.filter(email=email).exists():
            
#             user = User.objects.get(email=email)
#             uid = urlsafe_base64_encode(force_bytes(user.id))
#             print('Encoded UID', uid)
#             token = PasswordResetTokenGenerator().make_token(user)
#             print('Password Reset Token', token)
#             link = 'http://localhost:3000/api/user/reset-password/' + uid + '/' + token
#             print('Password Reset Link', link)

#             #SEND Email
#             email_data = {
#                 'email_subject': 'Reset Your Password',
#                 'email_body': f'Click Following Link to Reset Your Password {link}',
#                 'to_email': user.email
#             }
#             Util.send_email(email_data)

#             return data
        
#         else:
#             raise serializers.ValidationError('User does not exist')
        

class SendResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']

    def validate(self, data):
        email = data.get('email')
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('User does not exist')
        return data



class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255, style={'input_type': 'password'}, write_only=True)
    confirm_password = serializers.CharField(max_length=255, style={'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password']

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError('Passwords do not match')
        return data


# class ResetPasswordSerializer(serializers.Serializer):
#     password = serializers.CharField(max_length=255, style={'input_type': 'password'}, write_only=True)
#     confirm_password = serializers.CharField(max_length=255, style={'input_type': 'password'}, write_only=True)

#     class Meta:
#         fields = ['password', 'confirm_password']

#     def validate(self, data):
#         password = data.get('password')
#         confirm_password = data.get('confirm_password')
#         if password != confirm_password:
#             raise serializers.ValidationError('Passwords do not match')
#         return data
    
#     def save(self, **kwargs):
#         try:
#             uid = self.context.get('uid')
#             token = self.context.get('token')
#             password = self.validated_data.get('password')
#             id = smart_str(urlsafe_base64_decode(uid))
#             user = User.objects.get(id=id)
#             if not PasswordResetTokenGenerator().check_token(user, token):
#                 raise serializers.ValidationError('Link is not valid or expired')
#             user.set_password(password)
#             user.save()
#             return user
#         except DjangoUnicodeDecodeError as identifier:
#             PasswordResetTokenGenerator().check_token(user, token)
#             raise serializers.ValidationError('Link is not valid or expired')
    



