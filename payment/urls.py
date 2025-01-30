from django.urls import path
from payment.views import PaymentProcess, PaymentVerify

urlpatterns = [
    path('initialize_payment/', PaymentProcess.as_view(), name='payment_process'),
    path('payment_verify/<str:reference>/', PaymentVerify.as_view(), name='payment_verify'),
]