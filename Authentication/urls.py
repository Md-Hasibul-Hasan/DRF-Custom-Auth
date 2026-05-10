from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),


    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/<uid>/<token>/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend-verification'),
    
    path('auth/google/', views.GoogleLoginView.as_view(), name='google-login'),

    path('login/', views.LoginView.as_view(), name='login'),
    path('2fa/setup/', views.Setup2FAView.as_view(), name='setup-2fa'),
    path('2fa/enable/', views.Enable2FAView.as_view(), name='enable-2fa'),
    path('2fa/verify/', views.Verify2FAView.as_view(), name='verify-2fa'),
    path('2fa/disable/', views.Disable2FAView.as_view(), name='disable-2fa'),
    path('2fa/status/', views.Get2FAStatusView.as_view(), name='2fa-status'),


    path('login-history/', views.LoginHistoryView.as_view(), name='login-history'),
    path('active-sessions/',views.ActiveSessionsView.as_view(),name='active-sessions'),
    path('delete-session/<session_id>/',views.DeleteSessionView.as_view(),name='delete-session'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('logout-all/', views.LogoutAllDevicesView.as_view(), name='logout-all'),


    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('send-reset-password-email/', views.SendResetPasswordEmailView.as_view(), name='send-reset-password-email'),
    path('reset-password/<uid>/<token>/', views.ResetPasswordView.as_view(), name='reset-password'),
    


    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-email/request/', views.ChangeEmailView.as_view(), name='request-change-email'),
    path('change-email/confirm/', views.ConfirmChangeEmailView.as_view(), name='confirm-change-email'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete-account'),

    


]