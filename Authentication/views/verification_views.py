from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.encoding import DjangoUnicodeDecodeError, force_bytes, smart_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import *
from ..serializers import *
from ..utils import Util
from ..renderers import UserRenderer
from .throttles import VerificationRateThrottle


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
                
                if user.verify_verification_otp(otp):
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
            
            # Generate new verification OTP
            otp = user.generate_verification_otp()
            
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
