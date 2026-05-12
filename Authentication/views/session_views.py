from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import *
from ..serializers import *
from ..renderers import UserRenderer


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
