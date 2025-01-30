from django.urls import path
from .views import InitializePayment, VerifyPayment, RefundTransaction
from .webhooks import paystack_webhook

urlpatterns = [
    path('initialize/', InitializePayment.as_view(), name='initialize_payment'),
    path('verify/<str:reference>/', VerifyPayment.as_view(), name='verify_payment'),
    path('refund/<str:reference>/', RefundTransaction.as_view(), name='refund_transaction'),
    path('webhook/', paystack_webhook, name='paystack_webhook'),
]
