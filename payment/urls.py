# payment/urls.py

from django.urls import path
from .views import (
    InitiatePaymentView,
    VerifyPaymentView,
    RefundPaymentView,
)
from .webhook_views import paystack_webhook

urlpatterns = [
    path('initialize/', InitiatePaymentView.as_view(), name='payment-initialize'),
    path('verify/', VerifyPaymentView.as_view(), name='payment-verify'),
    path('refund/<str:reference>/', RefundPaymentView.as_view(), name='payment-refund'),
    path('webhook/', paystack_webhook, name='paystack-webhook'),  # ✅ This creates /api/payments/webhook/
]