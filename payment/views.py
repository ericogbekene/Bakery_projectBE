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

# payment/views.py

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
        
        # ✅ Use the callback URL from settings
        callback_url = settings.PAYSTACK_CALLBACK_URL
        
        payload = {
            "email": email,
            "amount": int(amount * 100),
            "reference": reference,
            "callback_url": callback_url,
            "metadata": metadata or {}
        }
        
        print(f"📡 Paystack Payload: {payload}")
        print(f"📡 Callback URL: {callback_url}")
        
        try:
            response = requests.post(
                f"{cls.BASE_URL}/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=30
            )
            print(f"📡 Paystack Response Status: {response.status_code}")
            print(f"📡 Paystack Response: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Paystack Request Error: {e}")
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
        # ✅ DEBUG: Log authentication info
        print("=" * 60)
        print("🔐 PAYMENT INITIALIZATION DEBUG")
        print(f"Authorization Header: {request.headers.get('Authorization', 'Not provided')}")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else False}")
        print(f"User ID: {request.user.id if hasattr(request.user, 'id') else 'None'}")
        print(f"User Email: {request.user.email if hasattr(request.user, 'email') else 'None'}")
        print(f"Request Data: {request.data}")
        print("=" * 60)
        
        # ✅ Validate serializer
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"❌ Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_number = serializer.validated_data['order_number']
        print(f"🔍 Order number from request: {order_number}")

        # ✅ Get order by number only (don't require user match)
        try:
            order = Order.objects.get(order_number=order_number)
            print(f"✅ Order found: {order.id} - {order.order_number}")
        except Order.DoesNotExist:
            print(f"❌ Order not found: {order_number}")
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ If order was created by guest (no user), associate with authenticated user
        if not order.user:
            print(f"🔍 Guest order detected - associating with user {request.user.email}")
            order.user = request.user
            order.save()
            
            # Create history entry
            OrderHistory.objects.create(
                order=order,
                action='status_changed',
                description=f"Guest order associated with user {request.user.email} during payment",
                changed_by=request.user,
                old_value='guest',
                new_value='authenticated'
            )

        # ✅ Check if user owns the order now
        if order.user != request.user and not request.user.is_staff:
            print(f"❌ Permission denied: User {request.user.email} does not own order {order.order_number}")
            return Response({
                'error': 'You do not have permission to pay for this order.'
            }, status=status.HTTP_403_FORBIDDEN)

        # ✅ Check order status
        if order.status != 'pending':
            print(f"❌ Order status invalid: {order.status}")
            return Response({
                'error': f'Cannot initiate payment for order with status: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if order already has a completed payment
        if order.payment_status == 'paid':
            print(f"❌ Order already paid: {order.payment_status}")
            return Response(
                {'error': 'This order has already been paid for.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Generate unique transaction reference
        tx_ref = str(uuid.uuid4())
        customer_email = request.user.email or order.customer_email
        print(f"🔍 Transaction reference: {tx_ref}")
        print(f"🔍 Customer email: {customer_email}")
        print(f"🔍 Amount: {float(order.total_amount)}")

        # ✅ Create transaction record
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
        print(f"✅ Transaction created: {transaction.id}")

        # ✅ Initialize Paystack payment
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

        # ✅ Store the complete response
        transaction.gateway_response = result
        transaction.save()
        
        print(f"🔍 Paystack response status: {result.get('status')}")
        print(f"🔍 Paystack response data: {result.get('data', {})}")

        if result.get('status') and result.get('data', {}).get('authorization_url'):
            # Update transaction with Paystack-specific data
            transaction.paystack_access_code = result['data'].get('access_code', '')
            transaction.save()
            
            print(f"✅ Payment link generated: {result['data']['authorization_url']}")
            
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
            print(f"❌ Paystack initialization failed: {error_message}")
            
            return Response({
                'error': error_message,
                'details': result
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# VERIFY PAYMENT (PAYSTACK)
# ============================================================================

# payment/views.py

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
        # ✅ DEBUG: Log verification info
        print("=" * 60)
        print("🔐 PAYMENT VERIFICATION DEBUG")
        print(f"Query Params: {request.query_params}")
        print("=" * 60)
        
        # ✅ Use VerifyPaymentSerializer for validation
        serializer = VerifyPaymentSerializer(data=request.query_params)
        if not serializer.is_valid():
            print(f"❌ Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reference = serializer.validated_data.get('reference') or serializer.validated_data.get('trxref')
        
        if not reference:
            print("❌ No reference provided")
            return Response(
                {'error': 'Reference parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"🔍 Verifying reference: {reference}")

        try:
            transaction = Transaction.objects.get(reference=reference)
            print(f"✅ Transaction found: {transaction.id}")
        except Transaction.DoesNotExist:
            print(f"❌ Transaction not found: {reference}")
            return Response(
                {'error': 'Transaction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Don't re-verify already completed transactions
        if transaction.status == 'completed':
            print(f"ℹ️ Transaction already completed: {transaction.status}")
            return Response({
                'message': 'Payment already verified.',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)

        # Verify with Paystack
        paystack_service = PaystackService()
        result = paystack_service.verify_payment(reference)
        
        print(f"🔍 Paystack verification response status: {result.get('status')}")
        
        # Store verification response
        transaction.gateway_response = result
        transaction.save()

        if result.get('status') and result.get('data', {}).get('status') == 'success':
            paystack_data = result['data']
            
            # Verify amount matches to prevent fraud (convert to kobo for comparison)
            expected_amount = int(transaction.amount * 100)
            actual_amount = paystack_data.get('amount', 0)
            
            print(f"🔍 Expected amount (kobo): {expected_amount}")
            print(f"🔍 Actual amount (kobo): {actual_amount}")
            
            if actual_amount == expected_amount:
                # Update transaction
                transaction.status = 'completed'
                transaction.paystack_transaction_id = str(paystack_data.get('id', ''))
                transaction.save()
                print(f"✅ Transaction updated to completed")

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
                    print(f"✅ Order updated: {order.order_number} - status: confirmed, payment: paid")

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
                        print(f"✅ Cart deactivated: {order.cart.id}")

                # Send payment confirmation email
                send_payment_confirmation_email(transaction)
                print(f"✅ Confirmation email sent")

                # ✅ Return response with VerifyPaymentSerializer data
                response_data = VerifyPaymentSerializer({
                    'status': 'success',
                    'message': 'Payment verified successfully.',
                    'transaction': TransactionSerializer(transaction).data
                }).data

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                # Amount mismatch — possible fraud attempt
                print(f"❌ Amount mismatch! Expected: {expected_amount}, Actual: {actual_amount}")
                transaction.status = 'failed'
                transaction.save()

                if transaction.order:
                    transaction.order.payment_status = 'failed'
                    transaction.order.save()

                send_payment_failed_email(transaction)

                response_data = VerifyPaymentSerializer({
                    'status': 'failed',
                    'message': 'Payment verification failed. Amount mismatch.',
                    'expected_amount_kobo': expected_amount,
                    'actual_amount_kobo': actual_amount
                }).data

                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Payment failed or not successful
            print(f"❌ Payment verification failed: {result.get('message', 'Unknown error')}")
            transaction.status = 'failed'
            transaction.save()

            if transaction.order:
                transaction.order.payment_status = 'failed'
                transaction.order.save()

            # Send payment failed email
            send_payment_failed_email(transaction)

            response_data = VerifyPaymentSerializer({
                'status': 'failed',
                'message': 'Payment verification failed.',
                'details': result.get('message', 'Unknown error')
            }).data

            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

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
        print("=" * 60)
        print("🔐 REFUND INITIALIZATION DEBUG")
        print(f"Reference: {reference}")
        print(f"User: {request.user}")
        print("=" * 60)
        
        try:
            transaction = Transaction.objects.get(reference=reference)
            print(f"✅ Transaction found: {transaction.id}")
        except Transaction.DoesNotExist:
            print(f"❌ Transaction not found: {reference}")
            return Response(
                {'error': 'Transaction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only completed transactions can be refunded
        if transaction.status != 'completed':
            print(f"❌ Transaction not completed: {transaction.status}")
            return Response({
                'error': f'Cannot refund a transaction with status: {transaction.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not transaction.paystack_transaction_id:
            print(f"❌ No Paystack transaction ID found")
            return Response(
                {'error': 'No Paystack transaction ID found for this transaction.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RefundPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')
        print(f"🔍 Refund reason: {reason}")

        # Initialize Paystack refund
        paystack_service = PaystackService()
        result = paystack_service.refund_payment(
            transaction_id=transaction.paystack_transaction_id,
            amount=float(transaction.amount),
            reason=reason
        )

        # Store refund response
        transaction.gateway_response = result
        transaction.save()
        
        print(f"🔍 Paystack refund response status: {result.get('status')}")

        if result.get('status'):
            # Update transaction
            transaction.status = 'refunded'
            transaction.save()
            print(f"✅ Transaction updated to refunded")

            # Update order
            if transaction.order:
                transaction.order.payment_status = 'refunded'
                transaction.order.save()
                print(f"✅ Order payment status updated to refunded")

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
            print(f"✅ Refund confirmation email sent")

            return Response({
                'message': 'Refund initiated successfully.',
                'transaction': TransactionSerializer(transaction).data,
                'refund_response': result.get('data')
            }, status=status.HTTP_200_OK)
        else:
            error_message = result.get('message', 'Unknown error')
            print(f"❌ Refund failed: {error_message}")
            return Response({
                'error': 'Refund failed.',
                'details': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
