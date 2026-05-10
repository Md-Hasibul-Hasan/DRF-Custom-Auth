import os
from django.core.mail import EmailMessage


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], 
            body=data['email_body'], 
            from_email=os.environ.get('EMAIL_USER'),
            to=[data['to_email']]
        )
        email.send()





from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken
)


from .models import UserSession


def logout_all_user_sessions(user):

    # Blacklist all refresh tokens
    outstanding_tokens = OutstandingToken.objects.filter(
        user=user
    )

    for token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(
            token=token
        )

    # Mark sessions inactive
    UserSession.objects.filter(
        user=user
    ).update(is_active=False)