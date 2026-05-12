# 🔐 DRF Advanced Authentication System

![Django](https://img.shields.io/badge/Django-6.0-green)
![DRF](https://img.shields.io/badge/DRF-REST_Framework-red)
![JWT](https://img.shields.io/badge/Auth-JWT-blue)
![Security](https://img.shields.io/badge/Security-Advanced-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

A complete enterprise-level authentication system built with Django REST Framework and JWT.

Includes:

- JWT Authentication
- Session-aware JWT validation
- Email verification
- OTP authentication
- 2FA
- Google OAuth
- Multi-device session management
- Token blacklisting
- Login history tracking
- Device tracking
- Password reset via OTP & email
- Logout from all devices

---

# 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [Authentication Flow](#-authentication-flow)
- [API Endpoints](#-api-endpoints)
- [Protected Route Headers](#-protected-route-headers)
- [Recommended Testing Order](#-recommended-testing-order)
- [Postman Testing Guide](#-postman-testing-guide)
- [Security Features](#-security-features)
- [Project Structure](#-project-structure)

---

# ✨ Features

## 🔑 Authentication

- JWT Authentication
- Access & Refresh Tokens
- Refresh Token Rotation
- Token Blacklisting
- Session-aware JWT Authentication
- Google OAuth Login

---

## 📧 Email Verification

- Email Verification Link
- OTP Verification
- OTP Expiration
- OTP Attempt Locking
- Resend Verification
- Spam Protection

---

## 🔐 Two-Factor Authentication (2FA)

- Email-based OTP 2FA
- Enable / Disable 2FA
- Login Verification via OTP
- 2FA Attempt Locking
- 2FA Audit Logs

---

## 🔄 Session Management

- Multi-device Login
- Active Session Tracking
- Device Fingerprinting
- Browser & OS Detection
- Logout Specific Device
- Logout All Devices
- Session Revocation

---

## 👤 User Features

- Profile Management
- Change Password
- Change Email with OTP
- Delete Account
- Upload Profile Image

---

## 📊 Security & Monitoring

- Login History
- Failed Login Tracking
- IP Address Logging
- User-Agent Tracking
- Rate Limiting
- Account Locking
- Password Validation

---

# 🏗️ Architecture

```text
Client
   ↓
JWT Authentication Layer
   ↓
Custom SessionJWTAuthentication
   ↓
Authentication Views
   ↓
Database Models
   ├── User
   ├── UserSession
   ├── LoginHistory
   └── TwoFALog
```

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/drf-advanced-auth.git
cd drf-advanced-auth
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 5. Create Superuser

```bash
python manage.py createsuperuser
```

---

## 6. Run Server

```bash
python manage.py runserver
```

---

# ⚙️ Environment Variables

Create `.env`

```env
DEBUG=True

SECRET_KEY=your_secret_key

ALLOWED_HOSTS=127.0.0.1,localhost

FRONTEND_URL=http://localhost:3000

EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_password

OTP_EXPIRE_TIMEOUT=600
OTP_LOCKED_TIMEOUT=1800
MAX_WRONG_OTP_ATTEMPTS=5

GOOGLE_CLIENT_ID=your_google_client_id
```

---

# 🔄 Authentication Flow

## Registration Flow

```text
Register
   ↓
Verification Email + OTP Sent
   ↓
User Verifies Email
   ↓
Account Activated
```

---

## Login Flow (Without 2FA)

```text
Login
   ↓
Generate Access + Refresh Tokens
   ↓
Create UserSession
   ↓
Login Success
```

---

## Login Flow (With 2FA)

```text
Login
   ↓
Generate 2FA OTP
   ↓
Verify OTP
   ↓
Generate Access + Refresh Tokens
   ↓
Create UserSession
```

---

## Logout Flow

```text
Logout
   ↓
Blacklist Refresh Token
   ↓
Deactivate UserSession
   ↓
Access Token Invalidated
```

---

# 📡 API Endpoints

## Base URL

```text
http://127.0.0.1:8000/api/user/
```

---

# 🔑 Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register/` | Register user |
| POST | `/login/` | Login |
| POST | `/logout/` | Logout current device |
| POST | `/logout-all/` | Logout all devices |
| POST | `/auth/google/` | Google Login |

---

# 📧 Verification Endpoints

| Method | Endpoint |
|---|---|
| POST | `/verify-email/<uid>/<token>/` |
| POST | `/verify-otp/` |
| POST | `/resend-verification/` |

---

# 🔐 2FA Endpoints

| Method | Endpoint |
|---|---|
| POST | `/2fa/setup/` |
| POST | `/2fa/enable/` |
| POST | `/2fa/verify/` |
| POST | `/2fa/disable/` |
| GET | `/2fa/status/` |

---

# 🔄 Session Endpoints

| Method | Endpoint |
|---|---|
| GET | `/active-sessions/` |
| DELETE | `/delete-session/<id>/` |
| GET | `/login-history/` |

---

# 👤 Profile Endpoints

| Method | Endpoint |
|---|---|
| GET | `/profile/` |
| PATCH | `/profile/` |
| POST | `/change-email/request/` |
| POST | `/change-email/confirm/` |
| DELETE | `/delete-account/` |

---

# 🔑 Password Endpoints

| Method | Endpoint |
|---|---|
| POST | `/change-password/` |
| POST | `/send-reset-password-email/` |
| POST | `/reset-password/<uid>/<token>/` |
| POST | `/reset-password-by-otp/` |

---

# 🎫 JWT Token Endpoints

| Method | Endpoint |
|---|---|
| POST | `/token/refresh/` |
| POST | `/token/verify/` |

---

# 🔐 Protected Route Headers

```text
Authorization: Bearer access_token
Content-Type: application/json
```

---

# 🧪 Recommended Testing Order

1. Register
2. Verify OTP
3. Login
4. Setup 2FA
5. Enable 2FA
6. Login Again
7. Verify 2FA
8. Active Sessions
9. Logout
10. Refresh Token
11. Change Password
12. Reset Password
13. Change Email
14. Delete Session
15. Logout All

---

# 🧪 Postman Testing Guide

---

# 1️⃣ Register

## Endpoint

```http
POST /register/
```

## Body

```json
{
  "name": "Hasib",
  "email": "hasib@gmail.com",
  "password": "Hasib123",
  "password2": "Hasib123"
}
```

---

## ✅ Success Response

```json
{
  "msg": "Registration successful. Please check your email to verify and activate your account using the link or OTP."
}
```

---

## ❌ Invalid Response

```json
{
  "errors": {
    "password": [
      "Password must contain at least one uppercase letter"
    ]
  }
}
```

---

# 2️⃣ Verify Email Using Link

## Endpoint

```http
POST /verify-email/<uid>/<token>/
```

---

## ✅ Success Response

```json
{
  "msg": "Email verified successfully"
}
```

---

## ❌ Invalid Link

```json
{
  "error": "Token is invalid or expired"
}
```

---

# 3️⃣ Verify OTP

## Endpoint

```http
POST /verify-otp/
```

## Body

```json
{
  "email": "hasib@gmail.com",
  "otp": "123456"
}
```

---

## ✅ Success Response

```json
{
  "msg": "OTP verified successfully. You can now log in."
}
```

---

## ❌ Invalid Response

```json
{
  "error": "Invalid or expired OTP"
}
```

---

# 4️⃣ Resend Verification

## Endpoint

```http
POST /resend-verification/
```

## Body

```json
{
  "email": "hasib@gmail.com"
}
```

---

## ✅ Success Response

```json
{
  "msg": "Verification email resent successfully"
}
```

---

## ❌ Spam Protection

```json
{
  "error": "Please wait 40 seconds before another request."
}
```

---

# 5️⃣ Login

## Endpoint

```http
POST /login/
```

## Body

```json
{
  "email": "hasib@gmail.com",
  "password": "Hasib123"
}
```

---

## ✅ Success Response

```json
{
  "msg": "Login Successful",
  "token": {
    "refresh": "refresh_token",
    "access": "access_token"
  }
}
```

---

## ✅ Login With 2FA Enabled

```json
{
  "requires_2fa": true,
  "temp_token": "temp_token_here"
}
```

---

## ❌ Invalid Credentials

```json
{
  "error": "Invalid email or password"
}
```

---

# 6️⃣ Verify 2FA

## Endpoint

```http
POST /2fa/verify/
```

## Body

```json
{
  "temp_token": "temp_token",
  "otp": "123456"
}
```

---

## ✅ Success Response

```json
{
  "msg": "2FA verification successful",
  "token": {
    "refresh": "refresh_token",
    "access": "access_token"
  }
}
```

---

# 7️⃣ Setup 2FA

## Endpoint

```http
POST /2fa/setup/
```

## Body

```json
{
  "method": "email"
}
```

---

## ✅ Response

```json
{
  "msg": "2FA setup initiated. Verification code sent."
}
```

---

# 8️⃣ Enable 2FA

## Endpoint

```http
POST /2fa/enable/
```

## Body

```json
{
  "otp": "123456"
}
```

---

## ✅ Response

```json
{
  "msg": "2FA enabled successfully"
}
```

---

# 9️⃣ Disable 2FA

## Endpoint

```http
POST /2fa/disable/
```

## Body

```json
{
  "password": "Hasib123"
}
```

---

## ✅ Response

```json
{
  "msg": "2FA disabled successfully"
}
```

---

# 🔟 Get 2FA Status

## Endpoint

```http
GET /2fa/status/
```

---

## ✅ Response

```json
{
  "is_2fa_enabled": true,
  "method": "email"
}
```

---

# 1️⃣1️⃣ Profile

## Endpoint

```http
GET /profile/
```

---

## ✅ Response

```json
{
  "id": 1,
  "email": "hasib@gmail.com",
  "name": "Hasib",
  "is_active": true
}
```

---

# 1️⃣2️⃣ Update Profile

## Endpoint

```http
PATCH /profile/
```

## Form Data

```text
name = Md Hasib
image = file
```

---

## ✅ Response

```json
{
  "msg": "Profile updated successfully"
}
```

---

# 1️⃣3️⃣ Active Sessions

## Endpoint

```http
GET /active-sessions/
```

---

## ✅ Response

```json
[
  {
    "id": 1,
    "browser": "Chrome",
    "operating_system": "Windows",
    "device_type": "Desktop",
    "this_device": true
  }
]
```

---

# 1️⃣4️⃣ Login History

## Endpoint

```http
GET /login-history/?limit=10
```

---

## ✅ Response

```json
[
  {
    "ip_address": "127.0.0.1",
    "user_agent": "Chrome",
    "login_time": "2026-05-12T10:00:00Z",
    "is_successful": true,
    "failure_reason": null
  }
]
```

---

# 1️⃣5️⃣ Logout Current Device

## Endpoint

```http
POST /logout/
```

## Body

```json
{
  "refresh": "refresh_token_here"
}
```

---

## ✅ Response

```json
{
  "msg": "Logged out successfully"
}
```

---

# 1️⃣6️⃣ Logout All Devices

## Endpoint

```http
POST /logout-all/
```

---

## ✅ Response

```json
{
  "msg": "Logged out from all devices successfully"
}
```

---

# 1️⃣7️⃣ Delete Specific Session

## Endpoint

```http
DELETE /delete-session/2/
```

---

## ✅ Response

```json
{
  "msg": "Session logged out successfully"
}
```

---

## ❌ Invalid

```json
{
  "error": "You cannot logout your current session"
}
```

---

# 1️⃣8️⃣ Change Password

## Endpoint

```http
POST /change-password/
```

## Body

```json
{
  "current_password": "Hasib123",
  "new_password": "NewPass123",
  "confirm_password": "NewPass123"
}
```

---

## ✅ Response

```json
{
  "msg": "Password Changed Successfully"
}
```

---

# 1️⃣9️⃣ Send Reset Password Email

## Endpoint

```http
POST /send-reset-password-email/
```

## Body

```json
{
  "email": "hasib@gmail.com"
}
```

---

## ✅ Response

```json
{
  "msg": "Password reset email sent successfully"
}
```

---

# 2️⃣0️⃣ Reset Password Using Link

## Endpoint

```http
POST /reset-password/<uid>/<token>/
```

## Body

```json
{
  "password": "NewPass123",
  "confirm_password": "NewPass123"
}
```

---

## ✅ Response

```json
{
  "msg": "Password Reset Successfully"
}
```

---

## ❌ Invalid Link

```json
{
  "error": "Link is not valid or expired"
}
```

---

# 2️⃣1️⃣ Reset Password By OTP

## Endpoint

```http
POST /reset-password-by-otp/
```

## Body

```json
{
  "email": "hasib@gmail.com",
  "otp": "123456",
  "password": "NewPass123",
  "confirm_password": "NewPass123"
}
```

---

## ✅ Response

```json
{
  "msg": "Password Reset Successfully"
}
```

---

# 2️⃣2️⃣ Change Email Request

## Endpoint

```http
POST /change-email/request/
```

## Body

```json
{
  "new_email": "new@gmail.com",
  "password": "Hasib123"
}
```

---

## ✅ Response

```json
{
  "msg": "OTP sent to the new email."
}
```

---

# 2️⃣3️⃣ Confirm Email Change

## Endpoint

```http
POST /change-email/confirm/
```

## Body

```json
{
  "new_email": "new@gmail.com",
  "otp": "123456"
}
```

---

## ✅ Response

```json
{
  "msg": "Email changed successfully"
}
```

---

# 2️⃣4️⃣ Delete Account

## Endpoint

```http
DELETE /delete-account/
```

## Body

```json
{
  "password": "Hasib123"
}
```

---

## ✅ Response

```json
{
  "msg": "Account deleted successfully"
}
```

---

# 2️⃣5️⃣ Refresh Token

## Endpoint

```http
POST /token/refresh/
```

## Body

```json
{
  "refresh": "refresh_token"
}
```

---

## ✅ Response

```json
{
  "access": "new_access_token",
  "refresh": "new_refresh_token"
}
```

---

# 2️⃣6️⃣ Verify Token

## Endpoint

```http
POST /token/verify/
```

## Body

```json
{
  "token": "access_token"
}
```

---

## ✅ Response

```json
{}
```

---

## ❌ Invalid Token

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

# 🔐 Important Security Behavior

After logout:

- refresh token becomes blacklisted
- session becomes inactive
- access token becomes unusable

Protected APIs after logout return:

```json
{
  "detail": "Session is inactive or expired."
}
```

---

# 🛡️ Security Features

- Session-aware JWT Authentication
- Refresh Token Blacklisting
- Multi-device Session Management
- OTP Expiration
- OTP Attempt Locking
- Login Rate Limiting
- Password Validation
- Account Locking
- Device Tracking
- IP Logging
- User-Agent Tracking
- Logout From All Devices
- Session Revocation

---

# 📂 Project Structure

```bash
Authentication/
│
├── models.py
├── serializers.py
├── authentication.py
├── utils.py
├── renderers.py
├── throttles.py
├── urls.py
│
├── views/
│   ├── auth_views.py
│   ├── password_views.py
│   ├── profile_views.py
│   ├── session_views.py
│   ├── token_views.py
│   └── two_factor_views.py
```

---

# 🚀 Future Improvements

- SMS OTP
- TOTP Authenticator App
- Redis Session Storage
- Docker Support
- Swagger / OpenAPI
- RBAC
- WebAuthn / Passkeys

---

# 👨‍💻 Author

## Md Hasibul Hasan

Backend Developer — Django & DRF

---

# 📜 License

MIT License