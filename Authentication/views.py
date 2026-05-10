from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from rest_framework_simplejwt.tokens import RefreshToken,AccessToken

from .models import *
from .serializers import *
from .utils import Util, logout_all_user_sessions
from .renderers import UserRenderer

from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken
)

import requests
from rest_framework.permissions import AllowAny


class LoginRateThrottle(UserRateThrottle):
    scope = 'login'
    # rate = '50/hour'  #in production use 5/hour


class RegisterRateThrottle(UserRateThrottle):
    scope = 'register'
    # rate = '30/hour' #in production use 5/hour


class PasswordResetRateThrottle(UserRateThrottle):
    scope = 'password-reset'
    # rate = '30/hour' #in production use 5/hour


class VerificationRateThrottle(UserRateThrottle):
    scope = 'verification'
    # rate = '50/hour' #in production use 5/hour


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


#Generate Token Manually
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }




class RegisterView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        dt=request.data
        serializer = RegistrationSerializer(data=dt)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            # Generate OTP
            otp = user.generate_otp()
            
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
    


class VerifyEmailView(APIView):
    throttle_classes = [VerificationRateThrottle]
    
    def post(self, request, uid, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"error": "Verification link is invalid or expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.is_active:
                return Response(
                    {"message": "Account already verified"},
                    status=status.HTTP_200_OK
                )

            user.is_active = True
            user.save()

            return Response(
                {"message": "Email verified successfully. You can now log in."},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class VerifyOTPView(APIView):
    throttle_classes = [VerificationRateThrottle]
    
    def post(self, request):
        dt = request.data
        serializer = VerifyOTPSerializer(data=dt)
        
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            otp = serializer.validated_data.get('otp')
            
            try:
                user = User.objects.get(email=email)
                
                if user.is_active:
                    return Response(
                        {"message": "Account already verified"},
                        status=status.HTTP_200_OK
                    )

                if user.otp_locked_until:
                    if timezone.now() < user.otp_locked_until:
                        return Response(
                            {
                                'error': (
                                    'Too many failed attempts. '
                                    'Try again later.'
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN
                        )               
                
                if user.verify_otp(otp):
                    user.is_active = True
                    user.save()
                    
                    return Response(
                        {"message": "OTP verified successfully. You can now log in."},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"error": "Invalid or expired OTP"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                        
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [LoginRateThrottle]

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
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        is_successful=False,
                        failure_reason='Account locked'
                    )
                    return Response(
                        {'error': 'Account is locked. Try again later.'},
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
                            'email_body': f'Your 2FA verification code is: {otp}\n\nThis code will expire in 5 minutes.',
                            'to_email': user.email
                        }
                        Util.send_email(email_data)

                        # Update last 2FA OTP sent timestamp
                        user.last_2fa_otp_sent_at = timezone.now()
                        user.save()
                        
                        # Create a temporary token for 2FA verification
                        # from rest_framework_simplejwt.tokens import RefreshToken
                        refresh = RefreshToken.for_user(user)
                        refresh['requires_2fa'] = True
                        refresh['exp'] = timezone.now() + timedelta(minutes=5)   # need to work here
                        
                        return Response({
                            'msg': '2FA verification required. Please check your email for the verification code',
                            'requires_2fa': True,
                            'temp_token': str(refresh.access_token),
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

                    UserSession.objects.create(
                        user=user,
                        refresh_token=token['refresh'],
                        session_jti=session_jti,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
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
    
    
class ProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                {
                    'msg': 'Profile updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class ChangePasswordView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        dt = request.data
        serializer = UserChangePasswordSerializer(
            data=dt,
            context={'user': user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            logout_all_user_sessions(user)

            email_data = {
                'email_subject': 'Password changed',
                'email_body': 'Your password was changed successfully.',
                'to_email': user.email
            }
            Util.send_email(email_data)

            return Response(
                {'msg': 'Password Changed Successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeEmailView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        dt = request.data
        serializer = ChangeEmailSerializer(
            data=dt,
            context={'user': user}
        )
        
        if serializer.is_valid(raise_exception=True):

            user = request.user

            # Prevent spam resend
            if user.last_email_change_otp_sent_at:
                seconds_passed = (
                    timezone.now() - user.last_email_change_otp_sent_at
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

            new_email = serializer.validated_data.get('new_email')

            otp = user.generate_pending_email_otp(new_email)

            email_data = {
                'email_subject': 'Confirm Your Email Change',
                'email_body': (
                    f'Your email change verification code is: '
                    f'{otp}\n\n'
                    f'This code will expire in 10 minutes.'
                ),
                'to_email': user.pending_email
            }

            Util.send_email(email_data)

            # Update last email change OTP sent timestamp
            user.last_email_change_otp_sent_at = timezone.now()
            user.save()

            return Response(
                {
                    'msg': (
                        'OTP sent to the new email. '
                        'Confirm the change with the OTP.'
                    )
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmChangeEmailView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        dt = request.data
        serializer = ConfirmChangeEmailSerializer(
            data=dt,
            context={'user': user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            email_data = {
                'email_subject': 'Email changed successfully',
                'email_body': 'Your email address has been updated successfully.',
                'to_email': user.email
            }
            Util.send_email(email_data)

            return Response(
                {'msg': 'Email changed successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class SendResetPasswordEmailView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        dt = request.data
        serializer = SendResetPasswordEmailSerializer(data=dt)

        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            try:
                user = User.objects.get(email=email)

                # Prevent spam resend
                if user.last_password_reset_sent_at:
                    seconds_passed = (
                        timezone.now() - user.last_password_reset_sent_at
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

                uid = urlsafe_base64_encode(force_bytes(user.id))
                token = PasswordResetTokenGenerator().make_token(user)

                reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

                email_data = {
                    'email_subject': 'Reset Your Password',
                    'email_body': f'Click the link to reset your password:\n{reset_link}',
                    'to_email': user.email,
                    'context': {
                        'subject': 'Reset your password',
                        'body': f'Please click the button below to reset your password.',
                        'cta_url': reset_link,
                        'cta_text': 'Reset Password',
                    }
                }
                Util.send_email(email_data)

                # Update last password reset sent timestamp
                user.last_password_reset_sent_at = timezone.now()
                user.save()

                return Response(
                    {'msg': 'Password reset link sent. Check your email.'},
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                # Don't reveal if email exists for security
                return Response(
                    {'msg': 'If email exists, password reset link has been sent.'},
                    status=status.HTTP_200_OK
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class ResetPasswordView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            try:
                user_id = smart_str(urlsafe_base64_decode(uid))
                user = User.objects.get(id=user_id)

                if not PasswordResetTokenGenerator().check_token(user, token):
                    return Response(
                        {'error': 'Link is not valid or expired'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                password = serializer.validated_data.get('password')
                user.set_password(password)
                user.save()

                logout_all_user_sessions(user)
                
                email_data = {
                    'email_subject': 'Password reset completed',
                    'email_body': 'Your password was reset successfully. If you did not perform this action, contact support.',
                    'to_email': user.email
                }
                Util.send_email(email_data)

                return Response(
                    {'msg': 'Password Reset Successfully'},
                    status=status.HTTP_200_OK
                )

            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            except DjangoUnicodeDecodeError as identifier:
                return Response(
                    {'error': 'Link is not valid or expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [VerificationRateThrottle]

    def post(self, request):
        dt = request.data
        serializer = ResendVerificationEmailSerializer(data=dt)

        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            user = User.objects.get(email=email)

            # Prevent spam resend
            if user.last_verification_otp_sent_at:
                seconds_passed = (
                    timezone.now() - user.last_verification_otp_sent_at
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
                

            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            # Generate new OTP
            otp = user.generate_otp()
            
            verify_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"

            email_data = {
                'email_subject': 'Verify your email (Resent) - Link and OTP',
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

            # Update last verification OTP sent timestamp
            user.last_verification_otp_sent_at = timezone.now()
            user.save()

            return Response(
                {'msg': 'Verification email resent with link and OTP. Check your email.'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginHistoryView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            limit = request.query_params.get('limit', 10)
            
            history = LoginHistory.objects.filter(user=user)[:int(limit)]
            
            data = [{
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'login_time': log.login_time.isoformat(),
                'is_successful': log.is_successful,
                'failure_reason': log.failure_reason
            } for log in history]
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to retrieve login history'},
                status=status.HTTP_400_BAD_REQUEST
            )



class ActiveSessionsView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-last_activity')

        current_jti = request.auth.payload.get('jti')

        serializer = UserSessionSerializer(
            sessions,
            many=True,
            context={
                'current_jti': current_jti
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

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


# Logout from specific device
class DeleteSessionView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):

        try:
            user = request.user

            current_jti = request.auth.payload.get('jti')

            # Find user's session
            session = UserSession.objects.get(
                id=session_id,
                user=user,
                is_active=True
            )

            # Prevent current session logout
            if session.session_jti == current_jti:
                return Response(
                    {
                        'error': 'You cannot logout your current session'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Blacklist refresh token
            token = RefreshToken(session.refresh_token)
            token.blacklist()

            # Mark session inactive
            session.is_active = False
            session.save()

            return Response(
                {
                    'msg': 'Session logged out successfully'
                },
                status=status.HTTP_200_OK
            )

        except UserSession.DoesNotExist:
            return Response(
                {
                    'error': 'Session not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception:
            return Response(
                {
                    'error': 'Failed to logout session'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class DeleteAccountView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

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
            from .models import TwoFALog
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
            from .models import TwoFALog
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
                from rest_framework_simplejwt.tokens import UntypedToken
                from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
                
                try:
                    decoded = UntypedToken(temp_token)
                    user_id = decoded['user_id']
                    user = User.objects.get(id=user_id)
                except (InvalidToken, TokenError, User.DoesNotExist):
                    return Response(
                        {'error': 'Invalid or expired temporary token'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Check if 2FA is locked
                if user.is_2fa_locked():
                    from .models import TwoFALog
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

                    UserSession.objects.create(
                        user=user,
                        refresh_token=token['refresh'],
                        session_jti=session_jti,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request)
                    )
                    
                    # Log successful 2FA verification
                    from .models import TwoFALog
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
                    from .models import TwoFALog
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
            from .models import TwoFALog
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






class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get('access_token')

        if not access_token:
            return Response(
                {'error': 'access_token required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Google থেকে user info নাও
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if google_response.status_code != 200:
            return Response(
                {'error': 'Invalid Google token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        google_data = google_response.json()
        email = google_data.get('email')
        name = google_data.get('name', '')

        if not email:
            return Response(
                {'error': 'Google account does not have email'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # User খোঁজো অথবা তৈরি করো
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'is_active': True,
            }
        )

        if not created and not user.is_active:
            user.is_active = True
            user.save()

        # simplejwt দিয়ে token বানাও — exactly same format
        refresh = RefreshToken.for_user(user)

        token = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response({
            'msg': 'Login Successful',
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            }
        }, status=status.HTTP_200_OK)
