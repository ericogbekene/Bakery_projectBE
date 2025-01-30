from django.shortcuts import render
from decimal import Decimal
# import pypaystack
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from orders.models import Order



# paystack.api_key = settings.PAYSTACK_SECRET_KEY
# paystack.api_version = settings.PAYSTACK_API_VERSION


# def payment_process(request):
#     secret_key = sk_test_1071bbcd9a85a4e4ed723744aa679360b5625d50
#     order_id = request.session.get('order_id')
#     order = get_object_or_404(Order, id=order_id)
#     amount = int(order.get_total_cost().quantize(Decimal('0.00')) * 100)

#     callback_url = reverse('payment:payment_process')

#     if request.method == 'POST':
#         success_url =request.build_absolute_uri(reverse('payment:payment_complete'))
#         cancel_url = request.build_absolute_uri(reverse('payment:payment_cancelled'))

#         # paystack checkout session data

#         session_data = {
#             'mode': 'payment'
#             'client_ref'
#         }  



    
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import PaymentSerializer
from drf_yasg.utils import swagger_auto_schema


class PaymentProcess(APIView):

    @swagger_auto_schema(request_body=PaymentSerializer)  # This tells Swagger to expect the PaymentSerializer in the body
    def post(self, request):
        paystack_secret_key = "sk_test_1071bbcd9a85a4e4ed723744aa679360b5625d50"
        
        payment_serializer = PaymentSerializer(data=request.data)
        if payment_serializer.is_valid():
            amount = float(payment_serializer.data.get('amount'))
            email = payment_serializer.data.get('email')

            amount_in_kobo = int(amount * 100)

            data = {
                "email": email,
                "amount": amount_in_kobo,
                "callback_url": "https://www.google.com/",
            }

            headers = {
                "Authorization": f"Bearer {paystack_secret_key}",
                "Content-Type": "application/json"
            }

            url = "https://api.paystack.co/transaction/initialize"
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                # Parse the response to get the payment URL
                response_data = response.json()
                payment_url = response_data['data']['authorization_url']
                return Response({"payment_url": payment_url}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": response.json()}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"detail": payment_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
                
class PaymentVerify(APIView):
    def get(self, request, reference):
        """
        Verifies a Paystack transaction using the reference passed in the URL.
        """
        PAYSTACK_SECRET_KEY = "sk_test_1071bbcd9a85a4e4ed723744aa679360b5625d50" 
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('status') == True:
            transaction_data = response_data.get('data', {})
            if transaction_data.get('status') == 'success':
                return Response({
                    "detail": "Payment verified successfully.",
                    "transaction_data": transaction_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": response_data}, status=status.HTTP_400_BAD_REQUEST)