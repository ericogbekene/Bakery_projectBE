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
# PAYSTACK SERVICE
# ============================================================================

class PaystackService:
    """Service class for Paystack API integration"""
    
    BASE_URL = "https://api.paystack.co"
    
    @classmethod
    def initialize_payment(cls, email, amount, reference, metadata=None):
        """Initialize payment with Paystack"""
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo/cents
            "reference": reference,
            "callback_url": f"{settings.FRONTEND_URL}/payment/verify",
            "metadata": metadata or {}
        }
        
        try:
            response = requests.post(
                f"{cls.BASE_URL}/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=30
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": str(e)}
    
    @classmethod
    def verify_payment(cls, reference):
        """Verify payment with Paystack"""
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }
        
        try:
            response = requests.get(
                f"{cls.BASE_URL}/transaction/verify/{reference}",
                headers=headers,
                timeout=30
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": str(e)}
    
    @classmethod
    def refund_payment(cls, transaction_id, amount, reason=""):
        """Initiate refund with Paystack"""
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "transaction": transaction_id,
            "amount": int(amount * 100),  # Convert to kobo
            "reason": reason or "Customer request"
        }
        
        try:
            response = requests.post(
                f"{cls.BASE_URL}/refund",
                json=payload,
                headers=headers,
                timeout=30
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": str(e)}


# ============================================================================
# EMAIL HELPERS
# ============================================================================

def send_payment_confirmation_email(transaction):
    """Send confirmation email after successful payment."""
    try:
        send_mail(
            subject=f"Payment Confirmed - Order {transaction.order.order_number}",
            message=(
                f"Dear {transaction.order.customer_name},\n\n"
                f"Your payment has been confirmed successfully via Paystack.\n\n"
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
        pass


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
                f"A refund has been initiated for your order via Paystack.\n\n"
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
# INITIATE PAYMENT (PAYSTACK)
# ============================================================================

class InitiatePaymentView(APIView):
    """
    POST /api/payments/initialize/

    Initiate a Paystack payment for an existing order.
    Authenticated users only.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Initiate Payment",
        operation_description="Initiate a Paystack payment for an existing pending order.",
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

        # Initialize Paystack payment
        paystack_service = PaystackService()
        result = paystack_service.initialize_payment(
            email=customer_email,
            amount=float(order.total_amount),
            reference=tx_ref,
            metadata={
                "order_number": order.order_number,
                "user_id": request.user.id,
                "transaction_ref": tx_ref
            }
        )

        # Store the complete response
        transaction.gateway_response = result

        if result.get('status') and result.get('data', {}).get('authorization_url'):
            # Update transaction with Paystack-specific data
            transaction.paystack_access_code = result['data'].get('access_code', '')
            transaction.save()
            
            return Response({
                'message': 'Payment initiated successfully.',
                'payment_link': result['data']['authorization_url'],
                'reference': tx_ref,
                'order_number': order.order_number,
                'amount': str(order.total_amount),
            }, status=status.HTTP_200_OK)
        else:
            transaction.status = 'failed'
            transaction.save()
            
            error_message = result.get('message', 'Failed to initiate payment with Paystack.')
            return Response({
                'error': error_message,
                'details': result
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# VERIFY PAYMENT (PAYSTACK)
# ============================================================================

class VerifyPaymentView(APIView):
    """
    GET /api/payments/verify/?reference={reference}&trxref={trxref}

    Verify a Paystack payment after the user is redirected back.
    Public endpoint — called after Paystack redirect.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify Payment",
        operation_description="Verify a Paystack payment using the transaction reference after redirect.",
        manual_parameters=[
            openapi.Parameter('reference', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Paystack transaction reference'),
            openapi.Parameter('trxref', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Alternative reference (Paystack sends both)'),
        ],
        responses={
            200: openapi.Response(description="Payment verified successfully."),
            400: openapi.Response(description="Payment verification failed."),
            404: openapi.Response(description="Transaction not found."),
        }
    )
    def get(self, request):
        # Paystack sends both reference and trxref as query params
        reference = request.query_params.get('reference') or request.query_params.get('trxref')
        
        if not reference:
            return Response(
                {'error': 'Reference parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        # Verify with Paystack
        paystack_service = PaystackService()
        result = paystack_service.verify_payment(reference)
        
        # Store verification response
        transaction.gateway_response = result

        if result.get('status') and result.get('data', {}).get('status') == 'success':
            paystack_data = result['data']
            
            # Verify amount matches to prevent fraud (convert to kobo for comparison)
            expected_amount = int(transaction.amount * 100)
            actual_amount = paystack_data.get('amount', 0)
            
            if actual_amount == expected_amount:
                # Update transaction
                transaction.status = 'completed'
                transaction.paystack_transaction_id = str(paystack_data.get('id', ''))
                transaction.save()

                # Update order
                order = transaction.order
                if order:
                    order.payment_status = 'paid'
                    order.paystack_transaction_id = str(paystack_data.get('id', ''))
                    order.paystack_reference = reference
                    order.paystack_response = paystack_data
                    order.payment_date = timezone.now()
                    order.status = 'confirmed'
                    order.save()

                    OrderHistory.objects.create(
                        order=order,
                        action='payment_received',
                        description=f"Payment received via Paystack. Reference: {reference}",
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
                # Amount mismatch — possible fraud attempt
                transaction.status = 'failed'
                transaction.save()

                if transaction.order:
                    transaction.order.payment_status = 'failed'
                    transaction.order.save()

                send_payment_failed_email(transaction)

                return Response({
                    'error': 'Payment verification failed. Amount mismatch.',
                    'expected_amount_kobo': expected_amount,
                    'actual_amount_kobo': actual_amount
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Payment failed or not successful
            transaction.status = 'failed'
            transaction.save()

            if transaction.order:
                transaction.order.payment_status = 'failed'
                transaction.order.save()

            # Send payment failed email
            send_payment_failed_email(transaction)

            return Response({
                'error': 'Payment verification failed.',
                'details': result.get('message', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# REFUND PAYMENT (PAYSTACK)
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
        operation_description="Initiate a refund for a completed Paystack transaction. Admin only.",
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

        if not transaction.paystack_transaction_id:
            return Response(
                {'error': 'No Paystack transaction ID found for this transaction.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefundPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')

        # Initialize Paystack refund
        paystack_service = PaystackService()
        result = paystack_service.refund_payment(
            transaction_id=transaction.paystack_transaction_id,
            amount=float(transaction.amount),
            reason=reason
        )

        # Store refund response
        transaction.gateway_response = result

        if result.get('status'):
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
                    description=f"Refund initiated via Paystack by admin. Reason: {reason if reason else 'No reason provided'}",
                    changed_by=request.user,
                    old_value='paid',
                    new_value='refunded'
                )

            # Send refund confirmation email
            send_refund_confirmation_email(transaction, reason)

            return Response({
                'message': 'Refund initiated successfully.',
                'transaction': TransactionSerializer(transaction).data,
                'refund_response': result.get('data')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Refund failed.',
                'details': result.get('message', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)