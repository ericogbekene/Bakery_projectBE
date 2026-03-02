from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

from accounts.models import CustomUser
from accounts.serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Register",
        operation_description="Create a new user account. A verification email will be sent after registration.",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(description="Registration successful. Verification email sent."),
            400: openapi.Response(description="Validation error."),
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate and save a verification token
        verification_token = str(uuid.uuid4())
        user.verification_token = verification_token
        user.save()

        # Send verification email
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{verification_token}"
        send_mail(
            subject="Verify your email address",
            message=f"Thank you for registering. Please verify your email by clicking the link: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        # Do NOT return token — user must verify email first
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user_id': user.id,
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """Verify user email using token sent via email"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify Email",
        operation_description="Verify a user's email address using the token sent to their email.",
        responses={
            200: openapi.Response(description="Email verified successfully."),
            400: openapi.Response(description="Invalid or expired verification token."),
        }
    )
    def get(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
            user.is_verified = True
            user.verification_token = None
            user.save()
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Invalid or expired verification token."}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Login",
        operation_description="Authenticate with email and password to receive access and refresh tokens.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(description="Login successful."),
            401: openapi.Response(description="Invalid credentials."),
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = authenticate(
            email=request.data.get("email"),
            password=request.data.get("password")
        )
        if user:
            return Response({
                "message": "Login successful",
                "access": response.data.get("access"),
                "refresh": response.data.get("refresh"),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Request Password Reset",
        operation_description="Send a password reset link to the provided email address.",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(description="Password reset email sent if account exists."),
            400: openapi.Response(description="Invalid email format."),
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            send_mail(
                subject="Password Reset Request",
                message=f"Click the link to reset your password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            # Return same message to avoid email enumeration
            pass

        return Response(
            {"message": "If an account with that email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Confirm Password Reset",
        operation_description="Reset the user's password using the uidb64 and token from the reset link.",
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(description="Password reset successful."),
            400: openapi.Response(description="Invalid or expired token."),
        }
    )
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data['new_password']
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)