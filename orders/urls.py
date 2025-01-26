from django.urls import path
from . import views

urlpatterns = [
    path('payment/process/', views.PaymentProcessView.as_view(), name='payment_process'),
]