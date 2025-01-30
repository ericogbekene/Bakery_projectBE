import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from orders.models import Order  # Import Order model
from .models import Transaction
from .serializers import TransactionSerializer
from decouple import config


class InitializePayment(APIView):
    """
    Initializes a Paystack payment and stores transaction details in the database.
    """

    def post(self, request):
        email = request.data.get('email')
        amount = request.data.get('amount')
        order_id = request.data.get('order_id')  # Get Order ID from request

        try:
            order = Order.objects.get(id=order_id, paid=False)  # Ensure order exists & is unpaid
        except Order.DoesNotExist:
            return Response({"error": "Order not found or already paid"}, status=status.HTTP_400_BAD_REQUEST)

        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {config("PAYSTACK_SECRET_KEY")}',  # Use env variable
            'Content-Type': 'application/json',
        }
        data = {
            'email': email,
            'amount': int(amount * 100),  # Convert NGN to kobo
            'reference': f"ORD-{order.id}-{order.created.strftime('%Y%m%d%H%M%S')}",  # Unique reference
           # 'callback_url': f"{settings.FRONTEND_URL}/payment/callback/",
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response_data['status']:
            # Save transaction details in database
            transaction = Transaction.objects.create(
                order=order,
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
    Verifies a payment via Paystack and updates order status if successful.
    """

    def get(self, request, reference):
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {config("PAYSTACK_SECRET_KEY")}',
        }

        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response_data['status'] and response_data['data']['status'] == 'success':
            try:
                transaction = Transaction.objects.get(reference=reference)
            except Transaction.DoesNotExist:
                return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

            # Update transaction and order status
            transaction.status = 'success'
            transaction.save()

            order = transaction.order
            order.paid = True
            order.save()

            serializer = TransactionSerializer(transaction)
            return Response({"message": "Payment verified successfully", "transaction": serializer.data},
                            status=status.HTTP_200_OK)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class RefundTransaction(APIView):
    """
    Processes refunds for failed transactions.
    """

    def post(self, request, reference):
        try:
            transaction = Transaction.objects.get(reference=reference)
            if transaction.status != "failed":
                return Response({"error": "Only failed transactions can be refunded"},
                                status=status.HTTP_400_BAD_REQUEST)

            url = f"https://api.paystack.co/refund"
            headers = {
                "Authorization": f"Bearer {config('PAYSTACK_SECRET_KEY')}",
                "Content-Type": "application/json",
            }
            data = {"transaction": reference}

            response = requests.post(url, headers=headers, json=data)
            res_data = response.json()

            if res_data.get("status"):
                transaction.status = "refunded"
                transaction.save()
                return Response({"message": "Refund processed successfully"}, status=status.HTTP_200_OK)
            else:
                return Response(res_data, status=status.HTTP_400_BAD_REQUEST)

        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
