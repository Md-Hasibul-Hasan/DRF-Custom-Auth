from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.encoding import DjangoUnicodeDecodeError, force_bytes, smart_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from Authentication.authentication import SessionJWTAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import *
from ..serializers import *
from ..utils import Util, logout_all_user_sessions
from ..renderers import UserRenderer
from .throttles import PasswordResetRateThrottle

from drf_spectacular.utils import extend_schema


class ChangePasswordView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionJWTAuthentication]
    serializer_class = UserChangePasswordSerializer

    @extend_schema(request=UserChangePasswordSerializer)
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
                'email_body': 'Your password was changed successfully. Please login with your new password. If you did not perform this action, contact support.',
                'to_email': user.email
            }
            Util.send_email(email_data)

            return Response(
                {'msg': 'Password Changed Successfully. Please login with your new password.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendResetPasswordEmailView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [PasswordResetRateThrottle]
    permission_classes = [AllowAny]
    serializer_class = SendResetPasswordEmailSerializer

    @extend_schema(request=SendResetPasswordEmailSerializer)
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

                # Generate password reset OTP and include it with the link
                otp = user.generate_password_reset_otp()
                reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

                email_data = {
                    'email_subject': 'Reset Your Password',
                    'email_body': (
                        f'Click the link to reset your password:\n{reset_link}\n\n'
                        f'Or use this OTP to reset your password: {otp}\n\n'
                        'OTP is valid for 10 minutes.'
                    ),
                    'to_email': user.email,
                    'context': {
                        'subject': 'Reset your password',
                        'body': (
                            f'Click the button below to reset your password or use the OTP: {otp}.'
                        ),
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
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(request=ResetPasswordSerializer)
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
                    'email_body': 'Your password was reset successfully. Please login with your new password. If you did not perform this action, contact support.',
                    'to_email': user.email
                }
                Util.send_email(email_data)

                return Response(
                    {'msg': 'Password Reset Successfully. Please login with your new password.'},
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


class ResetPasswordWithOTPView(APIView):
    renderer_classes = [UserRenderer]
    throttle_classes = [PasswordResetRateThrottle]
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordWithOTPSerializer

    @extend_schema(request=ResetPasswordWithOTPSerializer)
    def post(self, request):
        serializer = ResetPasswordWithOTPSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            otp = serializer.validated_data.get('otp')
            password = serializer.validated_data.get('password')

            try:
                user = User.objects.get(email=email)

                if user.password_reset_otp_locked_until:
                    now = timezone.now()
                    if now < user.password_reset_otp_locked_until:
                        remaining_seconds = int(
                            (
                                user.password_reset_otp_locked_until - now
                            ).total_seconds()
                        )
                        return Response(
                            {
                                'error': (
                                    'Too many failed attempts. '
                                    f'Try again after {remaining_seconds} seconds.'
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN
                        )

                if user.verify_password_reset_otp(otp):
                    user.set_password(password)
                    user.save()
                    logout_all_user_sessions(user)

                    email_data = {
                        'email_subject': 'Password reset completed',
                        'email_body': (
                            'Your password was reset successfully. If you did not perform this action, contact support.'
                        ),
                        'to_email': user.email
                    }
                    Util.send_email(email_data)

                    return Response(
                        {'msg': 'Password Reset Successfully'},
                        status=status.HTTP_200_OK
                    )
                else:
                    now = timezone.now()
                    if (
                        user.password_reset_otp_locked_until and
                        now < user.password_reset_otp_locked_until
                    ):
                        remaining_seconds = int(
                            (
                                user.password_reset_otp_locked_until - now
                            ).total_seconds()
                        )
                        return Response(
                            {
                                'error': (
                                    'Too many failed attempts. '
                                    f'Try again after {remaining_seconds} seconds.'
                                )
                            },
                            status=status.HTTP_403_FORBIDDEN
                        )

                    return Response(
                        {'error': 'Invalid or expired OTP'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
