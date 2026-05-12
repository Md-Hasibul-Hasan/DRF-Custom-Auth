from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import UserSession


class SessionJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)

        if validated_token.get('requires_2fa') is True:
            raise InvalidToken(
                {
                    'detail': '2FA verification required.',
                    'code': 'token_not_valid',
                }
            )

        return validated_token

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        session_jti = validated_token.get('jti')

        if not session_jti:
            raise AuthenticationFailed(
                'Invalid session token.',
                code='invalid_session'
            )

        if not UserSession.objects.filter(
            user=user,
            session_jti=session_jti,
            is_active=True
        ).exists():
            raise AuthenticationFailed(
                'Session is inactive or expired.',
                code='inactive_session'
            )

        return user
