from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserRegistrationView,
    VerifyEmailView,
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
]
