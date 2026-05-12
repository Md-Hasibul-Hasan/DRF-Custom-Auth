# 🔐 DRF Advanced Authentication System

![Django](https://img.shields.io/badge/Django-6.0-green)
![DRF](https://img.shields.io/badge/DRF-REST_Framework-red)
![JWT](https://img.shields.io/badge/Auth-JWT-blue)
![Security](https://img.shields.io/badge/Security-Advanced-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

A complete enterprise-level authentication system built with Django REST Framework and JWT. Includes email verification, OTP authentication, 2FA, Google OAuth, multi-device session management, and comprehensive security features.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture & Flow](#-architecture--complete-auth-flow)
- [Setup & Installation](#-setup--installation)
- [API Endpoints](#-api-endpoints)
- [Testing Guide](#-testing-guide)
- [Security Considerations](#-security-considerations)

---

## ✨ Features

### 🔑 Authentication & Authorization
- **JWT Authentication** - Access & Refresh tokens with automatic rotation
- **Token Rotation** - Secure token refresh mechanism
- **Token Blacklisting** - Revoke tokens immediately on logout
- **Protected APIs** - Permission-based endpoint access
- **Google OAuth 2.0** - Social login integration
- **Secure Password Hashing** - PBKDF2 by default

### 📧 Email Verification
- **Verification Link** - Token-based email verification
- **OTP Verification** - 6-digit OTP with 10-minute expiration
- **Resend Capability** - Request new verification emails/OTPs
- **Spam Protection** - Rate limiting on resend requests
- **Email Templates** - Professional HTML email templates

### 🔐 Two-Factor Authentication (2FA)
- **Email-based OTP** - Secondary verification via email
- **Setup & Enable** - User-initiated 2FA configuration
- **Disable with Password** - Secure 2FA deactivation
- **Status Tracking** - Check 2FA enabled status
- **Attempt Limiting** - Lock after 5 failed attempts

### 👤 User Profile Management
- **Profile View** - Retrieve user information
- **Profile Update** - Update name and profile image
- **Image Upload** - Store profile pictures in `mediafiles/`
- **Email Change** - Change email with OTP verification
- **Account Deletion** - Secure account removal

### 🔄 Session Management
- **Multi-Device Sessions** - Track multiple active sessions
- **Device Fingerprinting** - Identify devices by browser/OS/IP
- **Session Details** - IP address, user agent, device metadata
- **Active Sessions List** - View all active sessions
- **Session Logout** - Logout from specific devices
- **Logout All Devices** - Single command logout from all sessions
- **Activity Tracking** - Last activity timestamp per session
- **Current Device Indicator** - Flag current session in list

### 📊 Login History & Tracking
- **Login History** - View all login attempts (successful & failed)
- **Failed Attempts** - Reason for failed login attempts
- **IP Tracking** - Store IP address for each login
- **User Agent** - Browser and device identification
- **Timestamp** - Precise login time tracking
- **Limit Results** - Query parameter for history pagination

### 🛡️ Advanced Security
- **Account Lockout** - Automatic lockout after 5 failed login attempts
- **Lockout Duration** - Configurable lockout period
- **OTP Rate Limiting** - Max 5 wrong OTP attempts before lock
- **Login Rate Throttling** - Prevent brute force attacks
- **Register Rate Throttling** - Prevent mass registration
- **CORS Protection** - Configurable CORS headers
- **Password Validation** - Minimum 8 chars, uppercase, numbers required
- **Refresh Token Security** - Stored securely with expiration

### 🔑 Password Management
- **Change Password** - Authenticated users can change password
- **Password Reset Link** - Token-based password reset via email
- **Reset with OTP** - Password reset using OTP verification
- **Password Validation** - Enforce strong password requirements
- **Token Expiration** - Time-limited reset links

---

## 🏗️ Architecture & Complete Auth Flow

### System Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  Django REST API            │
│  ┌─────────────────────────┐│
│  │ JWT Authentication      ││
│  │ (AccessToken/Refresh)   ││
│  └─────────────────────────┘│
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Authentication Views       │
│  ├─ Auth Views              │
│  ├─ Session Views           │
│  ├─ 2FA Views               │
│  ├─ Password Views          │
│  ├─ Profile Views           │
│  └─ Token Views             │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Models & Database          │
│  ├─ User                    │
│  ├─ UserSession             │
│  ├─ LoginHistory            │
│  └─ TwoFALog                │
└─────────────────────────────┘
```

### Complete Authentication Flow

#### 1️⃣ **Registration Flow**
```
User Registration
    ↓
Input: email, name, password, password_confirm
    ↓
Validation (password strength, email format)
    ↓
User Created (is_active=False)
    ↓
Generate Verification Link & OTP
    ↓
Send Email with Link + OTP
    ↓
User Clicks Link or Enters OTP
    ↓
Account Activated (is_active=True)
    ↓
Ready for Login ✅
```

#### 2️⃣ **Login Flow (Without 2FA)**
```
User Login
    ↓
Input: email, password
    ↓
Rate Limit Check (LoginRateThrottle)
    ↓
Account Lock Check
    ↓
Password Verification
    ↓
Generate Access & Refresh Tokens
    ↓
Create UserSession (device tracking)
    ↓
Log Login History
    ↓
Return: {access_token, refresh_token}
    ↓
Store Tokens on Client ✅
```

#### 3️⃣ **Login Flow (With 2FA Enabled)**
```
User Login
    ↓
Pass email/password validation
    ↓
2FA Enabled? YES
    ↓
Generate 2FA OTP
    ↓
Send OTP to email
    ↓
Return: {temp_token, message: "Enter 2FA code"}
    ↓
User Enters OTP
    ↓
Verify OTP (max 5 attempts)
    ↓
OTP Correct?
    ├─ YES → Generate Access & Refresh Tokens
    │        Create UserSession
    │        Return: {access_token, refresh_token} ✅
    │
    └─ NO → Increment attempts
             5 attempts? → Lock for 30 minutes
```

#### 4️⃣ **Protected API Request Flow**
```
Client Request with Access Token
    ↓
Extract Token from Authorization Header
    ↓
Validate Token Signature & Expiration
    ↓
Check Token Blacklist
    ↓
Token Valid?
    ├─ YES → Attach User to Request
    │        Process Request ✅
    │
    └─ NO → Return 401 Unauthorized
             Suggest Token Refresh
```

#### 5️⃣ **Token Refresh Flow**
```
Client Sends Refresh Token
    ↓
Validate Refresh Token
    ↓
Lookup UserSession by session_jti
    ↓
Session Active?
    ├─ YES → Generate New Access Token
    │        Update UserSession.last_activity
    │        Return: {access_token} ✅
    │
    └─ NO → Return 401 (Re-login required)
             Sessions logged out from all devices
```

#### 6️⃣ **Logout Flow**
```
Authenticated User → Logout
    ↓
Extract Current Session JTI
    ↓
Add Refresh Token to Blacklist
    ↓
Mark UserSession.is_active = False
    ↓
Return: {msg: "Logged out successfully"}
    ↓
Client Discards Tokens ✅

Alternative: Logout All Devices
    ↓
Blacklist ALL refresh tokens for user
    ↓
Deactivate ALL sessions for user
    ↓
User must re-login ✅
```

#### 7️⃣ **2FA Setup Flow**
```
Authenticated User → Setup 2FA
    ↓
Send OTP to email
    ↓
User Enters OTP
    ↓
OTP Valid?
    ├─ YES → Enable 2FA (is_2fa_enabled = True)
    │        Return: {message: "2FA enabled"} ✅
    │
    └─ NO → Return error (try again)
```

#### 8️⃣ **Password Reset Flow**
```
User Forgot Password
    ↓
Submit Email
    ↓
Generate Reset Token (expires in 24h)
    ↓
Send Reset Link via Email
    ↓
User Clicks Link & Enters New Password
    ↓
Validate Token & Expiration
    ↓
Update Password
    ↓
Blacklist All Refresh Tokens
    ↓
Logout from All Sessions ✅
    ↓
User Must Re-login
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Django 6.0+
- PostgreSQL or SQLite

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/Md-Hasibul-Hasan/DRF-Custom-Auth.git
cd DRF-Custom-Auth

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Run server
python manage.py runserver
```

### Environment Variables (.env)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# JWT
JWT_ACCESS_TOKEN_LIFETIME=5  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days
JWT_ALGORITHM=HS256

# Email (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend URL
FRONTEND_URL=http://localhost:3000

# OTP Settings
OTP_EXPIRE_TIMEOUT=600  # 10 minutes in seconds
MAX_WRONG_OTP_ATTEMPTS=5
OTP_LOCKED_TIMEOUT=1800  # 30 minutes in seconds

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# Security
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_LOCKOUT_DURATION=1800  # 30 minutes in seconds
```

---

## 📡 API Endpoints

### Base URL
```
http://localhost:8000/api/user/
```

---

### 🔑 **Authentication Endpoints**

#### 1. Register User
```http
POST /register/
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "password2": "SecurePass123"
}
```

**Response (201 Created):**
```json
{
  "message": "Registration successful. Please check your email to verify and activate your account using the link or OTP."
}
```

**Error Responses:**
- `400 Bad Request` - Invalid data or email already exists
- Validation errors for password strength

---

#### 2. Verify Email with Link
```http
GET /verify-email/<uid>/<token>/
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

---

#### 3. Verify Email with OTP
```http
POST /verify-otp/
Content-Type: application/json

{
  "email": "john@example.com",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid OTP
- `429 Too Many Requests` - Too many failed OTP attempts (locked for 30 minutes)

---

#### 4. Resend Verification Email/OTP
```http
POST /resend-verification/
Content-Type: application/json

{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification email sent successfully"
}
```

---

#### 5. Login
```http
POST /login/
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response without 2FA (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "john@example.com",
    "name": "John Doe"
  }
}
```

**Response with 2FA (200 OK):**
```json
{
  "temp_token": "temp-jwt-token-for-2fa",
  "message": "2FA code sent to your email"
}
```

**Error Responses:**
- `403 Forbidden` - Account not verified or account locked
- `401 Unauthorized` - Invalid credentials

---

#### 6. Google Login
```http
POST /auth/google/
Content-Type: application/json

{
  "google_token": "google-access-token"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "john@gmail.com",
    "name": "John Google"
  }
}
```

---

### 🔐 **Two-Factor Authentication (2FA) Endpoints**

#### 1. Setup 2FA
```http
POST /2fa/setup/
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "message": "2FA OTP sent to your email"
}
```

---

#### 2. Enable 2FA
```http
POST /2fa/enable/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "2FA enabled successfully"
}
```

---

#### 3. Verify 2FA During Login
```http
POST /2fa/verify/
Content-Type: application/json

{
  "temp_token": "temp-jwt-token",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

#### 4. Disable 2FA
```http
POST /2fa/disable/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "password": "YourPassword123"
}
```

**Response (200 OK):**
```json
{
  "message": "2FA disabled successfully"
}
```

---

#### 5. Get 2FA Status
```http
GET /2fa/status/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "is_2fa_enabled": true,
  "two_fa_method": "email"
}
```

---

### 🔄 **Session Management Endpoints**

#### 1. Active Sessions
```http
GET /active-sessions/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "browser": "Chrome",
    "operating_system": "Windows",
    "device_type": "Desktop",
    "created_at": "2026-05-12T10:30:00Z",
    "last_activity": "2026-05-12T10:45:00Z",
    "is_active": true,
    "this_device": true
  },
  {
    "id": 2,
    "ip_address": "203.0.113.45",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)...",
    "browser": "Safari",
    "operating_system": "iOS",
    "device_type": "Mobile",
    "created_at": "2026-05-11T15:20:00Z",
    "last_activity": "2026-05-11T16:00:00Z",
    "is_active": true,
    "this_device": false
  }
]
```

---

#### 2. Delete Specific Session
```http
DELETE /delete-session/{session_id}/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "msg": "Session logged out successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Cannot logout current session
- `404 Not Found` - Session not found

---

#### 3. Logout from Single Device
```http
POST /logout/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "msg": "Logged out successfully"
}
```

---

#### 4. Logout from All Devices
```http
POST /logout-all/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "msg": "Logged out from all devices successfully"
}
```

---

### 📊 **Login History Endpoint**

#### Get Login History
```http
GET /login-history/?limit=10
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "login_time": "2026-05-12T10:30:00Z",
    "is_successful": true,
    "failure_reason": null
  },
  {
    "ip_address": "192.168.1.101",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6)...",
    "login_time": "2026-05-12T09:15:00Z",
    "is_successful": false,
    "failure_reason": "Invalid password"
  }
]
```

---

### 👤 **Profile Management Endpoints**

#### 1. Get Profile
```http
GET /profile/
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "john@example.com",
  "name": "John Doe",
  "image": "http://localhost:8000/mediafiles/profile_images/user1.jpg",
  "is_active": true
}
```

---

#### 2. Update Profile
```http
PUT /profile/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

{
  "name": "John Updated",
  "image": <binary-image-data>
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "john@example.com",
  "name": "John Updated",
  "image": "http://localhost:8000/mediafiles/profile_images/user1_updated.jpg",
  "is_active": true
}
```

---

#### 3. Change Email - Request
```http
POST /change-email/request/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "new_email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "OTP sent to your new email address"
}
```

---

#### 4. Change Email - Confirm
```http
POST /change-email/confirm/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Email changed successfully"
}
```

---

#### 5. Delete Account
```http
DELETE /delete-account/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "password": "YourPassword123"
}
```

**Response (200 OK):**
```json
{
  "message": "Account deleted successfully"
}
```

---

### 🔑 **Password Management Endpoints**

#### 1. Change Password
```http
POST /change-password/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_password": "OldPassword123",
  "new_password": "NewPassword456",
  "confirm_password": "NewPassword456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

---

#### 2. Send Password Reset Email
```http
POST /send-reset-password-email/
Content-Type: application/json

{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset email sent"
}
```

---

#### 3. Reset Password with Link
```http
POST /reset-password/{uid}/{token}/
Content-Type: application/json

{
  "password": "NewPassword456",
  "confirm_password": "NewPassword456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successfully"
}
```

---

#### 4. Reset Password with OTP
```http
POST /reset-password-by-otp/
Content-Type: application/json

{
  "email": "john@example.com",
  "otp": "123456",
  "password": "NewPassword456",
  "confirm_password": "NewPassword456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successfully"
}
```

---

### 🎫 **Token Management Endpoints**

#### 1. Refresh Access Token
```http
POST /token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access_token_lifetime": 300
}
```

---

#### 2. Verify Token
```http
POST /token/verify/
Content-Type: application/json

{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Token is invalid or expired"
}
```

---

## 🧪 Testing Guide

### Using Postman

#### Setup Postman Environment

1. Create new Environment: "DRF Auth"
2. Add variables:
   - `base_url`: `http://localhost:8000/api/user`
   - `access_token`: (will be populated)
   - `refresh_token`: (will be populated)
   - `temp_token`: (for 2FA testing)

#### Test Collection

**Collection: Authentication Tests**

---

### Complete Testing Workflow

#### **Test 1: Registration**

```bash
POST http://localhost:8000/api/user/register/

Headers:
Content-Type: application/json

Body:
{
  "name": "Test User",
  "email": "testuser@example.com",
  "password": "TestPass123",
  "password2": "TestPass123"
}

Expected Response: 201 Created
{
  "message": "Registration successful. Please check your email to verify and activate your account using the link or OTP."
}
```

---

#### **Test 2: Verify Email with OTP**

```bash
POST http://localhost:8000/api/user/verify-otp/

Headers:
Content-Type: application/json

Body:
{
  "email": "testuser@example.com",
  "otp": "123456"  # Check your email/console for OTP
}

Expected Response: 200 OK
{
  "message": "Email verified successfully"
}
```

---

#### **Test 3: Login (Without 2FA)**

```bash
POST http://localhost:8000/api/user/login/

Headers:
Content-Type: application/json

Body:
{
  "email": "testuser@example.com",
  "password": "TestPass123"
}

Expected Response: 200 OK
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "name": "Test User",
    "image": null,
    "is_active": true
  }
}

# Save access_token and refresh_token in Postman environment
```

---

#### **Test 4: Get Profile**

```bash
GET http://localhost:8000/api/user/profile/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
{
  "id": 1,
  "email": "testuser@example.com",
  "name": "Test User",
  "image": null,
  "is_active": true
}
```

---

#### **Test 5: Update Profile**

```bash
PUT http://localhost:8000/api/user/profile/

Headers:
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

Body (form-data):
name: Updated Test User
image: <select-image-file>

Expected Response: 200 OK
{
  "id": 1,
  "email": "testuser@example.com",
  "name": "Updated Test User",
  "image": "http://localhost:8000/mediafiles/profile_images/user1.jpg",
  "is_active": true
}
```

---

#### **Test 6: Setup 2FA**

```bash
POST http://localhost:8000/api/user/2fa/setup/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
{
  "message": "2FA OTP sent to your email"
}

# Check email for OTP
```

---

#### **Test 7: Enable 2FA**

```bash
POST http://localhost:8000/api/user/2fa/enable/

Headers:
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "otp": "123456"  # OTP from email
}

Expected Response: 200 OK
{
  "message": "2FA enabled successfully"
}
```

---

#### **Test 8: Get 2FA Status**

```bash
GET http://localhost:8000/api/user/2fa/status/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
{
  "is_2fa_enabled": true,
  "two_fa_method": "email"
}
```

---

#### **Test 9: Login with 2FA**

```bash
POST http://localhost:8000/api/user/login/

Headers:
Content-Type: application/json

Body:
{
  "email": "testuser@example.com",
  "password": "TestPass123"
}

Expected Response: 200 OK (2FA Required)
{
  "temp_token": "temp-jwt-token",
  "message": "2FA code sent to your email"
}

# Save temp_token
```

---

#### **Test 10: Verify 2FA**

```bash
POST http://localhost:8000/api/user/2fa/verify/

Headers:
Content-Type: application/json

Body:
{
  "temp_token": "<temp_token_from_previous_response>",
  "otp": "123456"  # 2FA OTP from email
}

Expected Response: 200 OK
{
  "access": "new-access-token",
  "refresh": "new-refresh-token"
}
```

---

#### **Test 11: Active Sessions**

```bash
GET http://localhost:8000/api/user/active-sessions/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
[
  {
    "id": 1,
    "ip_address": "127.0.0.1",
    "user_agent": "PostmanRuntime/7.x.x",
    "browser": "PostmanRuntime",
    "operating_system": "Unknown",
    "device_type": "Other",
    "created_at": "2026-05-12T10:30:00Z",
    "last_activity": "2026-05-12T10:45:00Z",
    "is_active": true,
    "this_device": true
  }
]
```

---

#### **Test 12: Login History**

```bash
GET http://localhost:8000/api/user/login-history/?limit=5

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
[
  {
    "ip_address": "127.0.0.1",
    "user_agent": "PostmanRuntime/7.x.x",
    "login_time": "2026-05-12T10:30:00Z",
    "is_successful": true,
    "failure_reason": null
  }
]
```

---

#### **Test 13: Change Password**

```bash
POST http://localhost:8000/api/user/change-password/

Headers:
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "current_password": "TestPass123",
  "new_password": "NewPass456",
  "confirm_password": "NewPass456"
}

Expected Response: 200 OK
{
  "message": "Password changed successfully"
}

# All sessions will be logged out
# You'll need to login again
```

---

#### **Test 14: Refresh Token**

```bash
POST http://localhost:8000/api/user/token/refresh/

Headers:
Content-Type: application/json

Body:
{
  "refresh": "{refresh_token}"
}

Expected Response: 200 OK
{
  "access": "new-access-token",
  "access_token_lifetime": 300
}
```

---

#### **Test 15: Logout Single Device**

```bash
POST http://localhost:8000/api/user/logout/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
{
  "msg": "Logged out successfully"
}

# This token becomes invalid
# You need refresh_token to get new access_token or login again
```

---

#### **Test 16: Delete Specific Session**

```bash
DELETE http://localhost:8000/api/user/delete-session/1/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
{
  "msg": "Session logged out successfully"
}

# That device/session is now logged out
```

---

#### **Test 17: Logout All Devices**

```bash
POST http://localhost:8000/api/user/logout-all/

Headers:
Authorization: Bearer {access_token}

Expected Response: 200 OK
{
  "msg": "Logged out from all devices successfully"
}

# All sessions terminated
# Must login again from any device
```

---

#### **Test 18: Password Reset - Send Email**

```bash
POST http://localhost:8000/api/user/send-reset-password-email/

Headers:
Content-Type: application/json

Body:
{
  "email": "testuser@example.com"
}

Expected Response: 200 OK
{
  "message": "Password reset email sent"
}

# Check email for reset link with uid and token
```

---

#### **Test 19: Password Reset - Using OTP**

```bash
# First, request password reset OTP
POST http://localhost:8000/api/user/send-reset-password-email/

Body:
{
  "email": "testuser@example.com"
}

# Then verify with OTP
POST http://localhost:8000/api/user/reset-password-by-otp/

Headers:
Content-Type: application/json

Body:
{
  "email": "testuser@example.com",
  "otp": "123456",  # OTP from email
  "password": "FinalPass789",
  "confirm_password": "FinalPass789"
}

Expected Response: 200 OK
{
  "message": "Password reset successfully"
}

# All sessions logged out
# Login with new password
```

---

#### **Test 20: Change Email**

```bash
# Step 1: Request email change
POST http://localhost:8000/api/user/change-email/request/

Headers:
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "new_email": "newemail@example.com"
}

Expected Response: 200 OK
{
  "message": "OTP sent to your new email address"
}

# Check new email for OTP

# Step 2: Confirm email change
POST http://localhost:8000/api/user/change-email/confirm/

Headers:
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "otp": "123456"  # OTP from new email
}

Expected Response: 200 OK
{
  "message": "Email changed successfully"
}

# Email is now updated
```

---

#### **Test 21: Disable 2FA**

```bash
POST http://localhost:8000/api/user/2fa/disable/

Headers:
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "password": "TestPass123"  # Current password (or updated password)
}

Expected Response: 200 OK
{
  "message": "2FA disabled successfully"
}

# 2FA is disabled
# Next login won't require 2FA
```

---

#### **Test 22: Delete Account**

```bash
DELETE http://localhost:8000/api/user/delete-account/

Headers:
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "password": "TestPass123"
}

Expected Response: 200 OK
{
  "message": "Account deleted successfully"
}

# Account is deleted
# Login with this email will fail
```

---

### Using cURL

#### Quick Test Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/user"

# 1. Register
echo "=== Testing Registration ==="
curl -X POST "$BASE_URL/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "testuser@example.com",
    "password": "TestPass123",
    "password2": "TestPass123"
  }'

# 2. Login
echo -e "\n\n=== Testing Login ==="
RESPONSE=$(curl -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123"
  }')

echo "$RESPONSE"

# Extract tokens (requires jq)
ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.access')
REFRESH_TOKEN=$(echo "$RESPONSE" | jq -r '.refresh')

# 3. Get Profile
echo -e "\n\n=== Testing Get Profile ==="
curl -X GET "$BASE_URL/profile/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Get Active Sessions
echo -e "\n\n=== Testing Active Sessions ==="
curl -X GET "$BASE_URL/active-sessions/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 5. Get Login History
echo -e "\n\n=== Testing Login History ==="
curl -X GET "$BASE_URL/login-history/?limit=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 6. Refresh Token
echo -e "\n\n=== Testing Refresh Token ==="
curl -X POST "$BASE_URL/token/refresh/" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh\": \"$REFRESH_TOKEN\"
  }"

# 7. Logout
echo -e "\n\n=== Testing Logout ==="
curl -X POST "$BASE_URL/logout/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

echo -e "\n\n=== Tests Completed ==="
```

---

### Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/user"

class AuthTester:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.session = requests.Session()
    
    def register(self, name, email, password):
        """Register a new user"""
        response = self.session.post(
            f"{BASE_URL}/register/",
            json={
                "name": name,
                "email": email,
                "password": password,
                "password2": password
            }
        )
        return response.json()
    
    def verify_otp(self, email, otp):
        """Verify email with OTP"""
        response = self.session.post(
            f"{BASE_URL}/verify-otp/",
            json={
                "email": email,
                "otp": otp
            }
        )
        return response.json()
    
    def login(self, email, password):
        """Login user"""
        response = self.session.post(
            f"{BASE_URL}/login/",
            json={
                "email": email,
                "password": password
            }
        )
        data = response.json()
        if "access" in data:
            self.access_token = data["access"]
            self.refresh_token = data["refresh"]
        return data
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.access_token}"
        }
    
    def get_profile(self):
        """Get user profile"""
        response = self.session.get(
            f"{BASE_URL}/profile/",
            headers=self.get_headers()
        )
        return response.json()
    
    def get_active_sessions(self):
        """Get active sessions"""
        response = self.session.get(
            f"{BASE_URL}/active-sessions/",
            headers=self.get_headers()
        )
        return response.json()
    
    def get_login_history(self, limit=10):
        """Get login history"""
        response = self.session.get(
            f"{BASE_URL}/login-history/?limit={limit}",
            headers=self.get_headers()
        )
        return response.json()
    
    def change_password(self, current_password, new_password):
        """Change password"""
        response = self.session.post(
            f"{BASE_URL}/change-password/",
            json={
                "current_password": current_password,
                "new_password": new_password,
                "confirm_password": new_password
            },
            headers=self.get_headers()
        )
        return response.json()
    
    def refresh_token(self):
        """Refresh access token"""
        response = self.session.post(
            f"{BASE_URL}/token/refresh/",
            json={
                "refresh": self.refresh_token
            }
        )
        data = response.json()
        if "access" in data:
            self.access_token = data["access"]
        return data
    
    def logout(self):
        """Logout"""
        response = self.session.post(
            f"{BASE_URL}/logout/",
            headers=self.get_headers()
        )
        return response.json()
    
    def logout_all(self):
        """Logout from all devices"""
        response = self.session.post(
            f"{BASE_URL}/logout-all/",
            headers=self.get_headers()
        )
        return response.json()

# Usage Example
if __name__ == "__main__":
    tester = AuthTester()
    
    # Test flow
    print("1. Registering user...")
    result = tester.register("Test User", "testuser@example.com", "TestPass123")
    print(json.dumps(result, indent=2))
    
    print("\n2. Logging in...")
    result = tester.login("testuser@example.com", "TestPass123")
    print(json.dumps(result, indent=2))
    
    print("\n3. Getting profile...")
    result = tester.get_profile()
    print(json.dumps(result, indent=2))
    
    print("\n4. Getting active sessions...")
    result = tester.get_active_sessions()
    print(json.dumps(result, indent=2))
    
    print("\n5. Getting login history...")
    result = tester.get_login_history()
    print(json.dumps(result, indent=2))
    
    print("\n6. Refreshing token...")
    result = tester.refresh_token()
    print(json.dumps(result, indent=2))
    
    print("\n7. Logging out...")
    result = tester.logout()
    print(json.dumps(result, indent=2))
```

---

## 🛡️ Security Considerations

### Best Practices Implemented

1. **Token Security**
   - Short-lived access tokens (5 minutes default)
   - Long-lived refresh tokens stored securely
   - Token blacklisting on logout
   - No tokens in URLs

2. **Password Security**
   - PBKDF2 hashing with Django's default hasher
   - Minimum 8 characters, uppercase, numbers required
   - Secure password reset with time-limited tokens
   - All sessions logout on password change

3. **Rate Limiting**
   - Login attempts throttled (5 per hour)
   - Registration throttled (10 per hour)
   - OTP resend limited (60 seconds between attempts)
   - Failed OTP attempts locked for 30 minutes after 5 attempts

4. **Account Protection**
   - Account lockout after 5 failed login attempts (30 minutes)
   - Email verification required before login
   - 2FA optional but recommended
   - Failed login logging and tracking

5. **Session Management**
   - Device fingerprinting
   - IP address tracking
   - User agent tracking
   - Multi-device logout capability
   - Current session protection (can't logout current session)

6. **Email Security**
   - OTP-based verification (6-digit codes)
   - Email change requires OTP verification
   - New device login notifications
   - Secure password reset emails

### Security Hardening Recommendations

```python
# In settings.py

# HTTPS only
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS - Restrict to specific domains
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
]

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Email backend with TLS
EMAIL_USE_TLS = True
EMAIL_PORT = 587
```

### Common Vulnerabilities Prevented

| Vulnerability | Prevention |
|---|---|
| SQL Injection | Django ORM (parameterized queries) |
| CSRF | Django CSRF middleware |
| XSS | DRF serializer validation |
| Brute Force | Rate throttling & account lockout |
| Token Theft | Token expiration & blacklisting |
| Email Enumeration | Generic error messages |
| Password Guessing | Strong password requirements |
| Session Hijacking | Device fingerprinting & 2FA |
| Account Takeover | Email verification & 2FA |

---

## 📝 License

MIT License - See LICENSE file for details

## 👥 Contributors

Md-Hasibul-Hasan

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Contact: your-email@example.com
- Secure Password Validation
- Logout From All Devices
- Logout From Specific Device

## 🛡️ Two-Factor Authentication (2FA)

- Email-based OTP Authentication
- Enable / Disable 2FA
- 2FA Verification During Login
- 2FA Audit Logs
- 2FA Attempt Locking

## 👤 User Features

- Profile Management
- Profile Image Upload
- Change Password
- Change Email with OTP Verification
- Delete Account

## 📊 Activity Tracking

- Login History
- Device Session Tracking
- IP Address Logging
- User-Agent Tracking

## ⚙️ Admin Features

- Fully Customized Django Admin
- User Session Monitoring
- Login History Monitoring
- 2FA Activity Logs
- Profile Image Preview

---

# 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 |
| API Framework | Django REST Framework |
| Authentication | SimpleJWT |
| Database | SQLite / PostgreSQL |
| Email Service | Django Email Backend |
| OAuth | Google OAuth |
| Security | JWT Blacklisting + Throttling |

---

# 📡 API Endpoints

## 🔐 Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth_api/register/` | Register user |
| POST | `/auth_api/login/` | Login user |
| POST | `/auth_api/logout/` | Logout current device |
| POST | `/auth_api/logout-all/` | Logout all devices |
| POST | `/auth_api/auth/google/` | Google login |

---

## 📧 Email Verification

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth_api/verify-email/<uid>/<token>/` | Verify email using link |
| POST | `/auth_api/verify-otp/` | Verify email using OTP |
| POST | `/auth_api/resend-verification/` | Resend verification email |

---

## 🔑 JWT Token APIs

| Method | Endpoint |
|---|---|
| POST | `/auth_api/token/` |
| POST | `/auth_api/token/refresh/` |
| POST | `/auth_api/token/verify/` |

---

## 👤 User Profile

| Method | Endpoint |
|---|---|
| GET | `/auth_api/profile/` |
| PATCH | `/auth_api/profile/` |

---

## 🔒 Password Management

| Method | Endpoint |
|---|---|
| POST | `/auth_api/change-password/` |
| POST | `/auth_api/send-reset-password-email/` |
| POST | `/auth_api/reset-password/<uid>/<token>/` |

---

## 📩 Email Change

| Method | Endpoint |
|---|---|
| POST | `/auth_api/change-email/request/` |
| POST | `/auth_api/change-email/confirm/` |

---

## 🛡️ Two-Factor Authentication

| Method | Endpoint |
|---|---|
| POST | `/auth_api/2fa/setup/` |
| POST | `/auth_api/2fa/enable/` |
| POST | `/auth_api/2fa/verify/` |
| POST | `/auth_api/2fa/disable/` |
| GET | `/auth_api/2fa/status/` |

---

## 📊 Activity & Session Management

| Method | Endpoint |
|---|---|
| GET | `/auth_api/login-history/` |
| GET | `/auth_api/active-sessions/` |
| DELETE | `/auth_api/delete-session/<id>/` |

---

## ❌ Account Management

| Method | Endpoint |
|---|---|
| POST | `/auth_api/delete-account/` |

---

# 🔄 Authentication Flow

## Registration Flow

1. User registers
2. Verification email sent
3. User verifies account via:
   - Verification link
   - OR OTP
4. Account becomes active

---

## Login Flow

### Without 2FA

1. User logs in
2. JWT tokens returned
3. Session created

### With 2FA

1. User logs in
2. OTP sent to email
3. User verifies OTP
4. JWT tokens returned

---

# 📦 Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/drf-advanced-auth.git
cd drf-advanced-auth
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 5️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

---

## 6️⃣ Run Development Server

```bash
python manage.py runserver
```

---

# ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_secret_key

EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_password
EMAIL_FROM=your_email@gmail.com

FRONTEND_URL=http://localhost:3000
```

---

# 🔐 JWT Configuration

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

---

# 🧪 Example Login Request

## Request

```json
{
  "email": "hasib@example.com",
  "password": "Password123"
}
```

---

## Response

```json
{
  "msg": "Login Successful",
  "token": {
    "refresh": "refresh_token_here",
    "access": "access_token_here"
  },
  "user": {
    "id": 1,
    "name": "Hasib",
    "email": "hasib@example.com"
  }
}
```

---

# 🛡️ Security Features Included

- JWT Authentication
- Refresh Token Rotation
- Refresh Token Blacklisting
- Account Lockout Protection
- OTP Expiration
- OTP Attempt Limiting
- Login Rate Limiting
- Password Validation
- Session Tracking
- Device Logout
- IP Address Logging

---

# 📂 Project Structure

```bash
DRF_Auth/
│
├── auth_api/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── utils.py
│   ├── views.py
│   ├── renderers.py
│
├── DRF_Auth/
│   ├── settings.py
│   ├── urls.py
│
├── mediafiles/
├── staticfiles/
├── manage.py
└── README.md
```

---

# 🚀 Future Improvements

- SMS-based OTP
- Authenticator App (TOTP)
- Redis Token Storage
- Docker Support
- Swagger / OpenAPI Documentation
- Email Templates
- OAuth Providers (GitHub/Facebook)
- Role-Based Access Control (RBAC)

---

# 👨‍💻 Author

**Md Hasibul Hasan**

Backend Developer — Django & DRF

---

# 📜 License

This project is intended for educational, portfolio, and production-learning purposes.