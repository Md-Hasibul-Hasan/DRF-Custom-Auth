from rest_framework.throttling import UserRateThrottle


class LoginRateThrottle(UserRateThrottle):
    scope = 'login'
    # rate = '50/hour'  #in production use 5/hour


class RegisterRateThrottle(UserRateThrottle):
    scope = 'register'
    # rate = '30/hour' #in production use 5/hour


class PasswordResetRateThrottle(UserRateThrottle):
    scope = 'password-reset'
    # rate = '30/hour' #in production use 5/hour


class VerificationRateThrottle(UserRateThrottle):
    scope = 'verification'
    # rate = '50/hour' #in production use 5/hour
