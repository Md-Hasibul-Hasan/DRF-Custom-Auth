import hashlib
import ipaddress
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import UserSession
from ..utils import Util

try:
    from user_agents import parse as parse_user_agent
except ImportError:
    parse_user_agent = None


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def is_public_ip(ip_address):
    try:
        parsed_ip = ipaddress.ip_address(ip_address)
    except (TypeError, ValueError):
        return False
    return parsed_ip.is_global


def decimal_or_none(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def get_ip_geolocation(ip_address):
    if not settings.GEOLOCATION_ENABLED or not is_public_ip(ip_address):
        return {}

    try:
        response = requests.get(
            f'https://ipapi.co/{ip_address}/json/',
            timeout=settings.GEOLOCATION_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return {}

    if data.get('error'):
        return {}

    return {
        'location_city': data.get('city') or '',
        'location_region': data.get('region') or '',
        'location_country': data.get('country_name') or '',
        'location_timezone': data.get('timezone') or '',
        'location_latitude': decimal_or_none(data.get('latitude')),
        'location_longitude': decimal_or_none(data.get('longitude')),
    }


#Generate Token Manually
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_device_metadata(request):
    user_agent = get_user_agent(request)
    ip_address = get_client_ip(request)

    if parse_user_agent:
        parsed_user_agent = parse_user_agent(user_agent)
        browser = parsed_user_agent.browser.family or 'Unknown Browser'
        operating_system = parsed_user_agent.os.family or 'Unknown OS'

        if parsed_user_agent.is_mobile:
            device_type = 'Mobile'
        elif parsed_user_agent.is_tablet:
            device_type = 'Tablet'
        elif parsed_user_agent.is_pc:
            device_type = 'Desktop'
        elif parsed_user_agent.is_bot:
            device_type = 'Bot'
        else:
            device_type = 'Unknown'
    else:
        browser = 'Unknown Browser'
        operating_system = 'Unknown OS'
        device_type = 'Unknown'

    return {
        'ip_address': ip_address,
        'user_agent': user_agent,
        'browser': browser,
        'operating_system': operating_system,
        'device_type': device_type,
        **get_ip_geolocation(ip_address),
    }


def generate_device_fingerprint(user, metadata):
    fingerprint_source = '|'.join(
        [
            str(user.id),
            metadata.get('user_agent') or '',
            metadata.get('browser') or '',
            metadata.get('operating_system') or '',
            metadata.get('ip_address') or '',
        ]
    )
    return hashlib.sha256(fingerprint_source.encode('utf-8')).hexdigest()


def send_new_device_login_email(user, metadata):
    login_time = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %I:%M %p')
    email_data = {
        'email_subject': 'New login detected on your account',
        'email_body': (
            'New login detected on your account.\n\n'
            f"Browser: {metadata.get('browser')}\n"
            f"OS: {metadata.get('operating_system')}\n"
            f"Device Type: {metadata.get('device_type')}\n"
            f"IP Address: {metadata.get('ip_address')}\n"
            f"Location: {format_location(metadata)}\n"
            f"Time: {login_time}\n\n"
            'If this was not you, please reset your password immediately.'
        ),
        'to_email': user.email,
        'context': {
            'subject': 'New login detected on your account',
            'body': (
                'New login detected on your account.\n\n'
                f"Browser: {metadata.get('browser')}\n"
                f"OS: {metadata.get('operating_system')}\n"
                f"Device Type: {metadata.get('device_type')}\n"
                f"IP Address: {metadata.get('ip_address')}\n"
                f"Location: {format_location(metadata)}\n"
                f"Time: {login_time}\n\n"
                'If this was not you, please reset your password immediately.'
            ),
            'cta_url': '',
            'cta_text': '',
        }
    }
    Util.send_email(email_data)


def format_location(metadata):
    location_parts = [
        metadata.get('location_city'),
        metadata.get('location_region'),
        metadata.get('location_country'),
    ]
    location = ', '.join(part for part in location_parts if part)
    return location or 'Unknown'


def create_user_session_with_device_tracking(user, request, token, session_jti):
    metadata = get_device_metadata(request)
    fingerprint = generate_device_fingerprint(user, metadata)
    is_new_device = not UserSession.objects.filter(
        user=user,
        device_fingerprint=fingerprint
    ).exists()

    user_session = UserSession.objects.create(
        user=user,
        refresh_token=token['refresh'],
        session_jti=session_jti,
        ip_address=metadata.get('ip_address'),
        user_agent=metadata.get('user_agent'),
        device_fingerprint=fingerprint,
        browser=metadata.get('browser'),
        operating_system=metadata.get('operating_system'),
        device_type=metadata.get('device_type'),
        location_city=metadata.get('location_city'),
        location_region=metadata.get('location_region'),
        location_country=metadata.get('location_country'),
        location_timezone=metadata.get('location_timezone'),
        location_latitude=metadata.get('location_latitude'),
        location_longitude=metadata.get('location_longitude'),
    )

    if is_new_device:
        send_new_device_login_email(user, metadata)

    return user_session
