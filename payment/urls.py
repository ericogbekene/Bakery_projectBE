from django.urls import path
from .views import (
    InitiatePaymentView,
    VerifyPaymentView,
    RefundPaymentView,
)

app_name = 'payments'

urlpatterns = [
    path('initialize/', InitiatePaymentView.as_view(), name='payment-initialize'),
    path('verify/<str:reference>/', VerifyPaymentView.as_view(), name='payment-verify'),
    path('refund/<str:reference>/', RefundPaymentView.as_view(), name='payment-refund'),
]