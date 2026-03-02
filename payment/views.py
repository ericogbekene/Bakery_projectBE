import requests
import uuid
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from orders.models import Order, OrderHistory
from .models import Transaction
from .serializers import (
    TransactionSerializer,
    InitiatePaymentSerializer,
    VerifyPaymentSerializer,
    RefundPaymentSerializer,
)


# ============================================================================
# EMAIL HELPERS (replaces tasks.py)
# ============================================================================

def send_payment_confirmation_email(transaction):
    """Send confirmation email after successful payment."""
    try:
        send_mail(
            subject=f"Payment Confirmed - Order {transaction.order.order_number}",
            message=(
                f"Dear {transaction.order.customer_name},\n\n"
                f"Your payment has been confirmed successfully.\n\n"
                f"Order Number: {transaction.order.order_number}\n"
                f"Amount Paid: ₦{transaction.amount:,.2f}\n"
                f"Transaction Reference: {transaction.reference}\n"
                f"Payment Date: {timezone.now().strftime('%d %B %Y, %I:%M %p')}\n\n"
                f"Your order is now being processed. We will notify you once it is ready.\n\n"
                f"Thank you for choosing M&C Cakes!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[transaction.email],
            fail_silently=True,
        )
    except Exception:
        pass  # Email failure should never block payment flow


def send_payment_failed_email(transaction):
    """Send notification email after failed payment."""
    try:
        send_mail(
            subject=f"Payment Failed - Order {transaction.order.order_number}",
            message=(
                f"Dear {transaction.order.customer_name},\n\n"
                f"Unfortunately, your payment could not be processed.\n\n"
                f"Order Number: {transaction.order.order_number}\n"
                f"Amount: ₦{transaction.amount:,.2f}\n"
                f"Transaction Reference: {transaction.reference}\n\n"
                f"Please try again or contact our support team for assistance.\n\n"
                f"M&C Cakes Support"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[transaction.email],
            fail_silently=True,
        )
    except Exception:
        pass


def send_refund_confirmation_email(transaction, reason=''):
    """Send confirmation email after refund is initiated."""
    try:
        send_mail(
            subject=f"Refund Initiated - Order {transaction.order.order_number}",
            message=(
                f"Dear {transaction.order.customer_name},\n\n"
                f"A refund has been initiated for your order.\n\n"
                f"Order Number: {transaction.order.order_number}\n"
                f"Refund Amount: ₦{transaction.amount:,.2f}\n"
                f"Transaction Reference: {transaction.reference}\n"
                f"Reason: {reason if reason else 'Not specified'}\n\n"
                f"Please allow 3-5 business days for the refund to reflect in your account.\n\n"
                f"M&C Cakes Support"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[transaction.email],
            fail_silently=True,
        )
    except Exception:
        pass


# ============================================================================
# INITIATE PAYMENT
# ============================================================================

class InitiatePaymentView(APIView):
    """
    POST /api/payments/initialize/

    Initiate a Flutterwave payment for an existing order.
    Authenticated users only.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Initiate Payment",
        operation_description="Initiate a Flutterwave payment for an existing pending order.",
        request_body=InitiatePaymentSerializer,
        responses={
            200: openapi.Response(description="Payment link generated successfully."),
            400: openapi.Response(description="Order cannot accept payment or validation error."),
            404: openapi.Response(description="Order not found."),
        }
    )
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_number = serializer.validated_data['order_number']

        try:
            order = Order.objects.get(
                order_number=order_number,
                user=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only pending orders can be paid for
        if order.status != 'pending':
            return Response({
                'error': f'Cannot initiate payment for order with status: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if order already has a completed payment
        if order.payment_status == 'paid':
            return Response(
                {'error': 'This order has already been paid for.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate unique transaction reference
        tx_ref = str(uuid.uuid4())
        customer_email = request.user.email

        # Create transaction record
        transaction = Transaction.objects.create(
            reference=tx_ref,
            order=order,
            cart=order.cart,
            email=customer_email,
            amount=order.total_amount,
            currency='NGN',
            user=request.user,
            status='pending'
        )

        # Prepare Flutterwave payload
        flutterwave_payload = {
            "tx_ref": tx_ref,
            "amount": str(order.total_amount),
            "currency": "NGN",
            "redirect_url": f"{settings.FRONTEND_URL}/payment/verify",
            "customer": {
                "email": customer_email,
                "name": order.customer_name,
                "phonenumber": request.user.phone_number or ""
            },
            "customizations": {
                "title": "M&C Cakes Payment",
                "description": f"Payment for Order {order.order_number}"
            },
            "meta": {
                "order_number": order.order_number,
                "user_id": request.user.id,
                "transaction_ref": tx_ref
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.flutterwave.com/v3/payments",
                json=flutterwave_payload,
                headers=headers,
                timeout=30
            )
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status') == 'success':
                return Response({
                    'message': 'Payment initiated successfully.',
                    'payment_link': response_data['data']['link'],
                    'tx_ref': tx_ref,
                    'order_number': order.order_number,
                    'amount': str(order.total_amount),
                }, status=status.HTTP_200_OK)
            else:
                transaction.status = 'failed'
                transaction.save()
                return Response({
                    'error': 'Failed to initiate payment with Flutterwave.',
                    'details': response_data
                }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            transaction.status = 'failed'
            transaction.save()
            return Response(
                {'error': f'Could not connect to Flutterwave: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


# ============================================================================
# VERIFY PAYMENT
# ============================================================================

class VerifyPaymentView(APIView):
    """
    GET /api/payments/verify/{reference}/

    Verify a Flutterwave payment after the user is redirected back.
    Public endpoint — called after Flutterwave redirect.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify Payment",
        operation_description="Verify a Flutterwave payment using the transaction reference after redirect.",
        responses={
            200: openapi.Response(description="Payment verified successfully."),
            400: openapi.Response(description="Payment verification failed."),
            404: openapi.Response(description="Transaction not found."),
        }
    )
    def get(self, request, reference):
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Don't re-verify already completed transactions
        if transaction.status == 'completed':
            return Response({
                'message': 'Payment already verified.',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)

        # Flutterwave sends transaction_id as query param after redirect
        flutterwave_tx_id = request.query_params.get('transaction_id')
        if not flutterwave_tx_id:
            return Response(
                {'error': 'transaction_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
        }

        try:
            response = requests.get(
                f"https://api.flutterwave.com/v3/transactions/{flutterwave_tx_id}/verify",
                headers=headers,
                timeout=30
            )
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'Could not connect to Flutterwave: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if response_data.get('status') != 'success':
            return Response(
                {'error': 'Failed to verify transaction with Flutterwave.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        flutterwave_data = response_data.get('data', {})

        # Verify amount and currency match to prevent fraud
        if (flutterwave_data.get('status') == 'successful'
                and float(flutterwave_data.get('amount', 0)) == float(transaction.amount)
                and flutterwave_data.get('currency') == transaction.currency):

            # Update transaction
            transaction.status = 'completed'
            transaction.flutterwave_transaction_id = str(flutterwave_tx_id)
            transaction.save()

            # Update order
            order = transaction.order
            if order:
                order.payment_status = 'paid'
                order.flutterwave_transaction_id = str(flutterwave_tx_id)
                order.flutterwave_reference = reference
                order.payment_date = timezone.now()
                order.status = 'confirmed'
                order.save()

                OrderHistory.objects.create(
                    order=order,
                    action='payment_received',
                    description=f"Payment received via Flutterwave. Reference: {reference}",
                    changed_by=transaction.user,
                    old_value='pending',
                    new_value='paid'
                )

                # Deactivate cart
                if order.cart:
                    order.cart.is_active = False
                    order.cart.save()

            # Send payment confirmation email
            send_payment_confirmation_email(transaction)

            return Response({
                'message': 'Payment verified successfully.',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)

        else:
            # Amount or currency mismatch — possible fraud attempt
            transaction.status = 'failed'
            transaction.save()

            if transaction.order:
                transaction.order.payment_status = 'failed'
                transaction.order.save()

            # Send payment failed email
            send_payment_failed_email(transaction)

            return Response({
                'error': 'Payment verification failed. Amount or currency mismatch.',
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# REFUND PAYMENT
# ============================================================================

class RefundPaymentView(APIView):
    """
    POST /api/payments/refund/{reference}/

    Initiate a refund for a completed transaction.
    Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Refund Payment (Admin)",
        operation_description="Initiate a refund for a completed Flutterwave transaction. Admin only.",
        request_body=RefundPaymentSerializer,
        responses={
            200: openapi.Response(description="Refund initiated successfully."),
            400: openapi.Response(description="Transaction cannot be refunded."),
            404: openapi.Response(description="Transaction not found."),
        }
    )
    def post(self, request, reference):
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only completed transactions can be refunded
        if transaction.status != 'completed':
            return Response({
                'error': f'Cannot refund a transaction with status: {transaction.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not transaction.flutterwave_transaction_id:
            return Response(
                {'error': 'No Flutterwave transaction ID found for this transaction.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefundPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        refund_payload = {
            "amount": str(transaction.amount)
        }

        try:
            response = requests.post(
                f"https://api.flutterwave.com/v3/transactions/{transaction.flutterwave_transaction_id}/refund",
                json=refund_payload,
                headers=headers,
                timeout=30
            )
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'Could not connect to Flutterwave: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if response_data.get('status') == 'success':
            # Update transaction
            transaction.status = 'refunded'
            transaction.save()

            # Update order
            if transaction.order:
                transaction.order.payment_status = 'refunded'
                transaction.order.save()

                OrderHistory.objects.create(
                    order=transaction.order,
                    action='refunded',
                    description=f"Refund initiated by admin. Reason: {reason if reason else 'No reason provided'}",
                    changed_by=request.user,
                    old_value='paid',
                    new_value='refunded'
                )

            # Send refund confirmation email
            send_refund_confirmation_email(transaction, reason)

            return Response({
                'message': 'Refund initiated successfully.',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                'error': 'Refund failed.',
                'details': response_data
            }, status=status.HTTP_400_BAD_REQUEST)