from django.urls import path
from .views import InitializePayment, VerifyPayment

urlpatterns = [
    path('initialize/', InitializePayment.as_view(), name='initialize_payment'),
    path('verify/<str:reference>/', VerifyPayment.as_view(), name='verify_payment'),
]