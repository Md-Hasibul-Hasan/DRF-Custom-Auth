from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from datetime import timedelta

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from Authentication.authentication import SessionJWTAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from ..models import *
from ..serializers import *
from ..utils import Util, logout_all_user_sessions
from ..renderers import UserRenderer
from .helpers import (
    create_user_session_with_device_tracking,
    get_client_ip,
    get_tokens_for_user,
    get_user_agent,
)
from .throttles import LoginRateThrottle, RegisterRateThrottle

from drf_spectacular.utils import extend_schema 




class RegisterView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [RegisterRateThrottle]
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer 

    @extend_schema(request=RegistrationSerializer)
    def post(self, request):
        dt=request.data
        serializer = RegistrationSerializer(data=dt)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            # Generate verification OTP
            otp = user.generate_verification_otp()
            
            verify_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"

            email_data = {
                'email_subject': 'Verify your email with link and OTP',
                'email_body': f'Click the link to verify your account:\n{verify_link}\n\nOr use this OTP: {otp}\n\nOTP is valid for 10 minutes.',
                'to_email': user.email,
                'context': {
                    'subject': 'Verify your email',
                    'body': f'Use the OTP below or click the button to verify your account:\n\nOTP: {otp}\n\nOTP is valid for 10 minutes.',
                    'cta_url': verify_link,
                    'cta_text': 'Verify Email',
                }
            }
            Util.send_email(email_data)

            return Response(
                {
                    "message": "Registration successful. Please check your email to verify and activate your account using the link or OTP."
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [LoginRateThrottle]
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(request=UserLoginSerializer)
    def post(self, request):
        dt = request.data
        serializer = UserLoginSerializer(data=dt)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            
            try:
                user = User.objects.get(email=email)
                
                # Check if account is locked
                if user.is_account_locked():
                    remaining_seconds = int(
                        (user.locked_until - timezone.now()).total_seconds()
                    )
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        is_successful=False,
                        failure_reason='Account locked'
                    )

                    
                    return Response(
                        {
                            'error': (
                                'Account is locked. '
                                f'Try again after {remaining_seconds} seconds.'
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
                

                if not user.is_active:
                    return Response(
                        {'error': 'Please verify your email first'},
                        status=status.HTTP_403_FORBIDDEN
                )

                # Check if user exists and password is correct
                if user.check_password(password):
                    # Reset failed attempts
                    user.failed_login_attempts = 0
                    user.last_login_ip = get_client_ip(request)
                    user.save()
                    
                    # Log successful login
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        is_successful=True
                    )
                    
                    # Check if 2FA is enabled
                    if user.is_2fa_enabled:
                        # Prevent spam resend for 2FA OTP
                        if user.last_2fa_otp_sent_at:
                            seconds_passed = (
                                timezone.now() - user.last_2fa_otp_sent_at
                            ).total_seconds()

                            if seconds_passed < 60:
                                remaining_seconds = int(60 - seconds_passed)
                                return Response(
                                    {
                                        'error': (
                                            f'Please wait {remaining_seconds} seconds before another request.'
                                        )
                                    },
                                    status=status.HTTP_429_TOO_MANY_REQUESTS
                                )

                        # Generate 2FA OTP and send via email
                        otp = user.generate_2fa_otp()
                        email_data = {
                            'email_subject': 'Your 2FA Verification Code',
                            'email_body': (
                                f'Your 2FA verification code is: {otp}\n\n'
                                f'This code will expire in {settings.OTP_EXPIRE_TIMEOUT // 60} minutes.'
                            ),
                            'to_email': user.email
                        }
                        Util.send_email(email_data)

                        # Update last 2FA OTP sent timestamp
                        user.last_2fa_otp_sent_at = timezone.now()
                        user.save()
                        
                        # Create a temporary token for 2FA verification
                        # from rest_framework_simplejwt.tokens import RefreshToken
                        temp_access = AccessToken.for_user(user)
                        temp_access.set_exp(lifetime=timedelta(minutes=5))
                        temp_access['requires_2fa'] = True
                        
                        return Response({
                            'msg': '2FA verification required. Please check your email for the verification code',
                            'requires_2fa': True,
                            'temp_token': str(temp_access),
                            'user': {
                                'id': user.id,
                                'name': user.name,
                                'email': user.email,
                            }
                        }, status=status.HTTP_200_OK)
                    
                    token = get_tokens_for_user(user)

                    # Create user session to track user activity
                    access = AccessToken(token['access'])
                    session_jti = str(access['jti'])

                    create_user_session_with_device_tracking(
                        user,
                        request,
                        token,
                        session_jti
                    )
                    return Response({
                        'msg': 'Login Successful', 
                        'token': token,
                        'user': {
                            'id': user.id,
                            'name': user.name,
                            'email': user.email,
                        }},
                        status=status.HTTP_200_OK
                    )
                else:
                    # Increment failed attempts
                    user.failed_login_attempts += 1
                    
                    # Lock account after MAX_LOGIN_ATTEMPTS
                    if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                        user.locked_until = timezone.now() + timedelta(seconds=settings.ACCOUNT_LOCKOUT_DURATION)
                    
                    user.save()
                    
                    # Log failed login
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        is_successful=False,
                        failure_reason='Invalid password'
                    )

                    if user.locked_until and timezone.now() < user.locked_until:
                        remaining_seconds = int(
                            (user.locked_until - timezone.now()).total_seconds()
                        )
                        return Response(
                            {
                                'error': (
                                    'Account is locked. '
                                    f'Try again after {remaining_seconds} seconds.'
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN
                        )
                    
                    return Response(
                        {'error': 'Invalid email or password'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid email or password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionJWTAuthentication]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer)
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Update the is_active field
            UserSession.objects.filter(
                refresh_token=refresh_token,
                user=request.user
            ).update(is_active=False)

            return Response(
                {'msg': 'Logged out successfully'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class LogoutAllDevicesView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionJWTAuthentication]

    def post(self, request):
        try:

            user = request.user
            logout_all_user_sessions(user)

            return Response(
                {
                    'msg': 'Logged out from all devices successfully'
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    'error': 'Failed to logout from all devices'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class DeleteAccountView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionJWTAuthentication]
    serializer_class = DeleteAccountSerializer

    @extend_schema(request=DeleteAccountSerializer)
    def post(self, request):
        try:
            user = request.user
            password = request.data.get('password')
            
            if not password:
                return Response(
                    {'error': 'Password is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not user.check_password(password):
                return Response(
                    {'error': 'Invalid password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            email = user.email
            email_data = {
                'email_subject': 'Account deleted',
                'email_body': 'Your account has been deleted successfully.',
                'to_email': user.email
            }
            Util.send_email(email_data)
            
            logout_all_user_sessions(user)

            user.delete()
            
            return Response(
                {'msg': f'Account {email} has been deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to delete account'},
                status=status.HTTP_400_BAD_REQUEST
            )
