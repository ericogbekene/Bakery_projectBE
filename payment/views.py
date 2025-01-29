import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction
from .serializers import TransactionSerializer

from decouple import config
from django.conf import settings



class InitializePayment(APIView):
    """
    This is the view that handles the payment process. It takes a POST request with
    the following parameters:
    - email: the email of the user
    - amount: the amount of the transaction in NGN
    - reference: a unique reference for the transaction
    """
    
    def post(self, request):
        email = request.data.get('email')
        amount = request.data.get('amount')
        
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',   
        }
        data = {
            'email': email,
            'amount': amount
        }
        
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        if response_data['status']:
            # save transaction details to the database
            
            transaction = Transaction.objects.create(
                email=email,
                amount=amount,
                reference=response_data['data']['reference'],
            )
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)




class VerifyPayment(APIView):
    """
    This is the view that handles the verification of a payment. It takes a POST request with
    the following parameters:
    - self: the view class
    - request: the request object
    - reference: a unique reference for the transaction
    """
    
    def get(self, request, reference):
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            
        }
        
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        if response_data['status'] and response_data['data']['status'] == 'success':
            
            # Update transaction status in the database
            
            transaction = Transaction.objects.get(reference=reference)
            transaction.status = 'success'
            transaction.save()
            
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
