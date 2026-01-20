from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/<uid>/<token>/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('send-reset-password-email/', views.SendResetPasswordEmailView.as_view(), name='send-reset-password-email'),
    path('reset-password/<uid>/<token>/', views.ResetPasswordView.as_view(), name='reset-password'),

]