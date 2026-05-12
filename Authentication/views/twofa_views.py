from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from ..models import *
from ..serializers import *
from ..utils import Util
from ..renderers import UserRenderer
from .helpers import (
    create_user_session_with_device_tracking,
    get_client_ip,
    get_tokens_for_user,
    get_user_agent,
)
from .throttles import VerificationRateThrottle



# 2FA Views
class Setup2FAView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    throttle_classes = [VerificationRateThrottle]

    def post(self, request):
        """Setup 2FA for authenticated user"""
        user = request.user
        serializer = Setup2FASerializer(data=request.data, context={'user': user})
        
        if serializer.is_valid(raise_exception=True):
            method = serializer.validated_data.get('method')
            
            # Prevent spam resend for 2FA setup OTP
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
            
            # Generate OTP for setup verification
            otp = user.generate_2fa_otp()
            
            # Send OTP to email
            email_data = {
                'email_subject': 'Setup Two-Factor Authentication',
                'email_body': f'Your 2FA setup verification code is: {otp}\n\nThis code will expire in 5 minutes. Do not share this code with anyone.',
                'to_email': user.email
            }
            Util.send_email(email_data)

            # Update last 2FA OTP sent timestamp
            user.last_2fa_otp_sent_at = timezone.now()
            user.save()
            
            # Log 2FA setup attempt
            from ..models import TwoFALog
            TwoFALog.objects.create(
                user=user,
                action='setup',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status='success'
            )
            
            return Response({
                'msg': f'2FA setup initiated. Verification code sent to {user.email}',
                'method': method
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Enable2FAView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    throttle_classes = [VerificationRateThrottle]

    def post(self, request):
        """Enable 2FA after verifying the setup code"""
        user = request.user
        serializer = Enable2FASerializer(data=request.data, context={'user': user})
        
        if serializer.is_valid(raise_exception=True):
            # Enable 2FA for user
            user.is_2fa_enabled = True
            user.two_fa_method = 'email'
            user.two_fa_otp = None
            user.two_fa_otp_created_at = None
            user.two_fa_otp_expires_at = None
            user.save()
            
            # Log 2FA enable
            from ..models import TwoFALog
            TwoFALog.objects.create(
                user=user,
                action='enable',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status='success'
            )
            
            return Response({
                'msg': '2FA has been successfully enabled for your account',
                'two_fa_enabled': True
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Verify2FAView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [VerificationRateThrottle]

    def post(self, request):
        """Verify 2FA code during login"""
        serializer = Verify2FASerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            temp_token = serializer.validated_data.get('temp_token')
            otp = serializer.validated_data.get('otp')
            
            try:
                # Decode the temporary token to get user
                from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
                
                try:
                    decoded = AccessToken(temp_token)
                    if decoded.get('requires_2fa') is not True:
                        return Response(
                            {'error': 'Invalid or expired temporary token'},
                            status=status.HTTP_401_UNAUTHORIZED
                        )
                    user_id = decoded['user_id']
                    user = User.objects.get(id=user_id)
                except (InvalidToken, TokenError, User.DoesNotExist):
                    return Response(
                        {'error': 'Invalid or expired temporary token'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Check if 2FA is locked
                if user.is_2fa_locked():
                    from ..models import TwoFALog
                    TwoFALog.objects.create(
                        user=user,
                        action='failed_attempt',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        status='failed'
                    )
                    return Response(
                        {'error': '2FA is temporarily locked due to too many failed attempts. Try again in 15 minutes.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Verify 2FA OTP
                if user.verify_2fa_otp(otp):
                    # Generate final access token
                    token = get_tokens_for_user(user)

                    # Create user session
                    access = AccessToken(token['access'])
                    session_jti = str(access['jti'])

                    create_user_session_with_device_tracking(
                        user,
                        request,
                        token,
                        session_jti
                    )
                    
                    # Log successful 2FA verification
                    from ..models import TwoFALog
                    TwoFALog.objects.create(
                        user=user,
                        action='verify',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        status='success'
                    )
                    
                    return Response({
                        'msg': '2FA verification successful',
                        'token': token,
                        'user': {
                            'id': user.id,
                            'name': user.name,
                            'email': user.email,
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    # Log failed 2FA verification
                    from ..models import TwoFALog
                    TwoFALog.objects.create(
                        user=user,
                        action='failed_attempt',
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        status='failed'
                    )
                    
                    return Response(
                        {'error': 'Invalid or expired 2FA code'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Disable2FAView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    throttle_classes = [VerificationRateThrottle]

    def post(self, request):
        """Disable 2FA for authenticated user"""
        user = request.user
        serializer = Disable2FASerializer(data=request.data, context={'user': user})
        
        if serializer.is_valid(raise_exception=True):
            # Disable 2FA
            user.is_2fa_enabled = False
            user.two_fa_method = None
            user.two_fa_otp = None
            user.two_fa_otp_created_at = None
            user.two_fa_otp_expires_at = None
            user.two_fa_attempts = 0
            user.two_fa_locked_until = None
            user.save()
            
            # Log 2FA disable
            from ..models import TwoFALog
            TwoFALog.objects.create(
                user=user,
                action='disable',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                status='success'
            )
            
            return Response({
                'msg': '2FA has been successfully disabled',
                'two_fa_enabled': False
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Get2FAStatusView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get 2FA status for authenticated user"""
        user = request.user
        
        return Response({
            'is_2fa_enabled': user.is_2fa_enabled,
            'two_fa_method': user.two_fa_method if user.is_2fa_enabled else None,
        }, status=status.HTTP_200_OK)
