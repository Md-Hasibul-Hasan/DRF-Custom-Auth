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