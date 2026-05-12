from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import *
from ..utils import Util
from ..renderers import UserRenderer


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
