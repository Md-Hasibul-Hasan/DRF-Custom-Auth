import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Util:
    @staticmethod
    def send_email(data):
        subject = data['email_subject']
        body = data['email_body']
        from_email = os.environ.get('EMAIL_USER')
        to_email = [data['to_email']]

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to_email,
        )

        template_name = data.get('template_name', 'Authentication/email_template.html')
        context = data.get('context', {
            'subject': subject,
            'body': body,
            'cta_url': data.get('cta_url', ''),
            'cta_text': data.get('cta_text', ''),
        })

        html_content = render_to_string(template_name, context)
        email.attach_alternative(html_content, 'text/html')
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