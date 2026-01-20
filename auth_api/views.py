from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import *
from .utils import Util
from .renderers import UserRenderer





#Generate Token Manually
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }




class RegisterView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request):
        dt=request.data
        serializer = RegistrationSerializer(data=dt)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            verify_link = f"http://localhost:3000/verify-email/{uid}/{token}/"

            email_data = {
                'email_subject': 'Verify your email',
                'email_body': f'Click the link to verify your account:\n{verify_link}',
                'to_email': user.email
            }
            Util.send_email(email_data)

            return Response(
                {
                    "message": "Registration successful. Please check your email to verify and activate your account."
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    






class VerifyEmailView(APIView):
    def post(self, request, uid, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"error": "Verification link is invalid or expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.is_active:
                return Response(
                    {"message": "Account already verified"},
                    status=status.HTTP_200_OK
                )

            user.is_active = True
            user.save()

            return Response(
                {"message": "Email verified successfully. You can now log in."},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class LoginView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request):

        dt = request.data
        serializer = UserLoginSerializer(data=dt)
        if serializer.is_valid(raise_exception=True):
            # Input নিতে হবে → serializer.validated_data 
            # Output দেখাতে হবে → serializer.data
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                token = get_tokens_for_user(user)
                return Response({
                    'msg': 'Login Successful', 
                    'token': token,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                    }},
                    status=status.HTTP_200_OK
                )
            else:
                return Response({
                    'errors':{'non_field_errors': ['Email or Password is not Valid']}
                },
                status=status.HTTP_400_BAD_REQUEST 
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ChangePasswordView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        dt = request.data
        serializer = UserChangePasswordSerializer(
            data=dt,
            context={'user': user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {'msg': 'Password Changed Successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# class SendResetPasswordEmailView(APIView):
#     renderer_classes = [UserRenderer]

#     def post(self,request):
#         dt = request.data
#         serializer = SendResetPasswordEmailSerializer(data=dt)
#         if serializer.is_valid(raise_exception=True):
#             return Response(
#                 {'msg': 'Password Reset Link Sent. Check Your Email'},
#                 status=status.HTTP_200_OK
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SendResetPasswordEmailView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request):
        dt = request.data
        serializer = SendResetPasswordEmailSerializer(data=dt)

        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"

            email_data = {
                'email_subject': 'Reset Your Password',
                'email_body': f'Click the link to reset your password:\n{reset_link}',
                'to_email': user.email
            }
            Util.send_email(email_data)

            return Response(
                {'msg': 'Password reset link sent. Check your email.'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class ResetPasswordView(APIView):
#     renderer_classes = [UserRenderer]

#     def post(self, request, uid, token):
#         dt = request.data 
#         serializer = ResetPasswordSerializer(data=dt, context={'uid': uid, 'token': token})
#         if serializer.is_valid(raise_exception=True):
#             serializer.save()
#             return Response(
#                 {'msg': 'Password Reset Successfully'},
#                 status=status.HTTP_200_OK
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ResetPasswordView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            try:
                user_id = smart_str(urlsafe_base64_decode(uid))
                user = User.objects.get(id=user_id)

                if not PasswordResetTokenGenerator().check_token(user, token):
                    return Response(
                        {'error': 'Link is not valid or expired'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                password = serializer.validated_data.get('password')
                user.set_password(password)
                user.save()

                return Response(
                    {'msg': 'Password Reset Successfully'},
                    status=status.HTTP_200_OK
                )

            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            except DjangoUnicodeDecodeError as identifier:
                return Response(
                    {'error': 'Link is not valid or expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


















    



