# DRF Custom Authentication API

![Django](https://img.shields.io/badge/Django-6.0-green)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.17-red)
![SimpleJWT](https://img.shields.io/badge/Auth-SimpleJWT-blue)
![Swagger](https://img.shields.io/badge/API_Docs-Swagger-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

A complete authentication architecture built with Django REST Framework. The project combines custom JWT authentication, session-aware token validation, OTP verification, two-factor authentication, device/session tracking, Google OAuth login, account protection, and API documentation.

Postman Docs: https://documenter.getpostman.com/view/48875561/2sBXqQFxV3

## Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Complete Workflow](#complete-workflow)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [API Endpoints](#api-endpoints)
- [Authentication Header](#authentication-header)
- [Cleanup Command](#cleanup-command)
- [Security Behavior](#security-behavior)
- [Project Structure](#project-structure)
- [Future Improvements](#future-improvements)

## ✨ Key Features

### 🔐 Authentication & Security
- **Custom JWT Authentication** - Custom token handling with rotation and validation
- **Session-Aware JWT Validation** - Sessions tracked and validated per device/browser
- **2FA Email-Based** - Additional security layer with email-based OTP verification
- **OAuth2 Integration** - Seamless Google login and registration
- **Rate Limiting & Lockout** - Automatic protection against brute force attacks
- **Security Notifications** - Real-time alerts for sensitive operations

### 📧 Email & Account Management
- **Dual Verification Methods** - OTP or activation link for email verification
- **Password Reset Flow** - Secure password recovery via OTP or reset link
- **Email Change Request** - Verified email change workflow
- **Profile Management** - Update user details and profile image

### 🖥️ Session & Device Management
- **Multi-Device Login** - Track and manage sessions across multiple devices
- **Login History** - Complete audit trail with IP, browser, OS details
- **Selective Logout** - Logout from specific device, selected sessions, or all devices
- **Device Tracking** - Identify browsers, OS, IP addresses, and user agents

### 🛡️ Advanced Protection
- **Token Blacklisting** - Invalidate tokens on logout or password change
- **Account Lockout** - Progressive lockout after failed attempts
- **Password Change Security** - Automatic logout from all devices on password change
- **Account Deletion** - Secure permanent account removal with data cleanup

### 📊 Developer Features
- **API Documentation** - Swagger, Redoc, and Postman integration
- **Management Commands** - Cleanup old sessions, logs, and tokens
- **PostgreSQL Ready** - Easy database switch from SQLite to PostgreSQL
- **CORS Support** - Django CORS headers for frontend integration

## Tech Stack

- Python
- Django
- Django REST Framework
- Django REST Framework SimpleJWT
- PostgreSQL-ready configuration
- SQLite for local development by default
- drf-spectacular for OpenAPI, Swagger, and Redoc
- Postman
- django-cors-headers
- WhiteNoise

## Architecture

```text
Client
  |
  v
Django REST Framework API
  |
  v
Custom Authentication Views
  |
  +-- JWT issue, refresh, rotation, and blacklist
  +-- Session-aware JWT validation
  +-- OTP verification and 2FA checks
  +-- Rate limiting and account lockout protection
  |
  v
Authentication Models
  |
  +-- User
  +-- UserSession
  +-- LoginHistory
  +-- TwoFALog
  +-- SimpleJWT token blacklist tables
```

## Complete Workflow

Users can register with name, email, and password. After registration, the API sends a verification email containing both an activation link and an OTP, allowing the account to be activated through either method.

Users log in with email and password. If 2FA is enabled, the login process returns a temporary token and requires OTP verification before access and refresh tokens are issued. Users can enable, disable, and check 2FA status from protected endpoints.

The system also supports Google OAuth login and registration. Authenticated users can update their profile, request an email change, change password, reset forgotten passwords, review active sessions, inspect login history, log out from selected devices, log out from all devices, or permanently delete their account.

Sensitive operations are logged and protected with rate limits, account lockout rules, token blacklisting, session deactivation, and security notifications.



## Security Behavior

After logout:

- The refresh token is blacklisted.
- The user session is marked inactive.
- Session-aware validation prevents access with tokens tied to inactive sessions.

After password change:

- Existing sessions are revoked.
- Other devices are logged out.
- The user must authenticate again with the new password.

Account protection includes:

- OTP expiration
- OTP attempt locking
- Login rate limiting
- Account lockout after repeated failures
- Device, browser, OS, IP address, and user-agent tracking
- Security logging for sensitive authentication events




## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/drf-custom-auth.git
cd drf-custom-auth
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## Environment Variables

Create a `.env` file in the project root.

```env
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

OTP_EXPIRE_TIMEOUT=600
MAX_WRONG_OTP_ATTEMPTS=5
OTP_LOCKED_UNTIL=600
PASSWORD_RESET_TIMEOUT=600

MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=600

GOOGLE_CLIENT_ID=your_google_client_id

LOGIN_HISTORY_RETENTION_DAYS=90
INACTIVE_SESSION_RETENTION_DAYS=30
TWO_FA_LOG_RETENTION_DAYS=30
```

PostgreSQL configuration is included in `DRF_Auth/settings.py` as a ready-to-enable database block. Local development currently uses SQLite by default.

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/api/schema/swagger-ui/
```

Redoc:

```text
http://127.0.0.1:8000/api/schema/redoc/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

Postman documentation:

```text
https://lnkd.in/gmfXCrxT
```

## API Endpoints

Base URL:

```text
http://127.0.0.1:8000/api/auth/
```

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/register/` | Register a new user |
| POST | `/login/` | Log in with email and password |
| POST | `/google-login/` | Google OAuth login or registration |
| POST | `/logout/` | Log out from the current device |
| POST | `/logout-all/` | Log out from all devices |

### Email Verification

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/verify-email/<uid>/<token>/` | Verify account using activation link |
| POST | `/verify-otp/` | Verify account using OTP |
| POST | `/resend-verification/` | Resend verification email and OTP |

### Two-Factor Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/2fa/setup/` | Start 2FA setup and send OTP |
| POST | `/2fa/enable/` | Enable 2FA after OTP verification |
| POST | `/2fa/verify/` | Complete login when 2FA is required |
| POST | `/2fa/disable/` | Disable 2FA |
| GET | `/2fa/status/` | Check current 2FA status |

### Sessions and Login History

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/active-sessions/` | List active sessions and devices |
| DELETE | `/delete-session/<session_id>/` | Log out from a specific session |
| GET | `/login-history/` | View login history |

### Profile and Account

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/profile/` | Get authenticated user profile |
| PATCH | `/profile/` | Update profile details and image |
| POST | `/change-email/request/` | Request email change OTP |
| POST | `/change-email/confirm/` | Confirm email change |
| DELETE | `/delete-account/` | Permanently delete account |

### Password

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/change-password/` | Change password while authenticated |
| POST | `/reset-password/request/` | Request password reset email and OTP |
| POST | `/reset-password/by-link/<uid>/<token>/` | Reset password using link |
| POST | `/reset-password/by-otp/` | Reset password using OTP |

### JWT Tokens

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/token/refresh/` | Refresh access token and rotate refresh token |
| POST | `/token/verify/` | Verify token validity |

## Authentication Header

Protected endpoints require a bearer token.

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```



## Cleanup Command

The project includes a management command for removing old authentication data and expired SimpleJWT tokens.

Dry run:

```bash
python manage.py cleanup_auth_tables --dry-run
```

Run cleanup:

```bash
python manage.py cleanup_auth_tables
```

Custom retention windows:

```bash
python manage.py cleanup_auth_tables --login-history-days 90 --inactive-session-days 30 --two-fa-log-days 30
```

The command cleans:

- Old `LoginHistory` records
- Inactive `UserSession` records
- Old `TwoFALog` records
- Expired SimpleJWT outstanding and blacklisted tokens


## Project Structure

```text
DRF_Custom_Auth/
  Authentication/
    authentication.py
    models.py
    renderers.py
    serializers.py
    throttles.py
    urls.py
    utils.py
    management/
      commands/
        cleanup_auth_tables.py
    views/
      auth_views.py
      password_views.py
      profile_views.py
      session_views.py
      token_views.py
      two_factor_views.py
  DRF_Auth/
    settings.py
    urls.py
  manage.py
  requirements.txt
  README.md
```

## Future Improvements

- SMS OTP support
- TOTP authenticator app support
- Redis-backed throttling and session cache
- Docker and Docker Compose setup
- Role-based access control
- WebAuthn/passkey authentication
- CI pipeline for tests and linting

## Author

Md Hasibul Hasan  
Backend Developer - Django & Django REST Framework

## License

MIT License
