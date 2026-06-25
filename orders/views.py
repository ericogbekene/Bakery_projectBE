from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.timezone import now
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal

from orders.models import Order, OrderHistory, OrderPayment
from orders.emails import (
    send_order_confirmation,
    send_order_status_update,
)
from cart.models import Cart, DeliveryInfo
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer,
    OrderCancelSerializer, OrderStatusUpdateSerializer, OrderPaymentUpdateSerializer
)


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an order or admins to view it.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if obj.user and obj.user == request.user:
            return True
        return False


class OrderListView(generics.ListAPIView):
    """
    GET /api/orders/
    List orders for the current user.
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            queryset = Order.objects.all()

            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            date_from = self.request.query_params.get('date_from')
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)

            date_to = self.request.query_params.get('date_to')
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

            return queryset.order_by('-created_at')

        return Order.objects.filter(user=user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """
    GET /api/orders/<id>/
    Get detailed information about a specific order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    permission_classes = [IsOrderOwnerOrAdmin]
    lookup_field = 'id'


class CreateOrderView(APIView):
    """
    POST /api/orders/create/
    Create an order from the current cart. Supports both guest and authenticated users.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Create Order",
        operation_description="Create a new order from the current cart. Works for both authenticated and guest users.",
        request_body=CreateOrderSerializer,
        responses={
            201: openapi.Response(description="Order created successfully."),
            400: openapi.Response(description="Validation error or empty cart."),
        }
    )
    @transaction.atomic
    def post(self, request):
        print("=" * 50)
        print("CREATE ORDER - RAW REQUEST")
        print("SESSION KEY:", request.session.session_key if hasattr(request, 'session') else 'NO SESSION')
        print("SESSION DATA:", dict(request.session) if hasattr(request, 'session') else {})
        print("AUTH HEADER:", request.headers.get('Authorization', 'None'))
        print("=" * 50)

        from cart.utils import get_or_create_cart
        cart = get_or_create_cart(request)

        print(f"🔍 Cart found: {cart.id}")
        print(f"🔍 Cart items: {cart.items.count()}")
        print(f"🔍 Cart user: {cart.user}")
        print(f"🔍 Cart is_active: {cart.is_active}")

        if cart.items.count() == 0:
            if request.user and request.user.is_authenticated:
                user_cart = Cart.objects.filter(
                    user=request.user,
                    is_active=True
                ).exclude(id=cart.id).first()

                if user_cart and user_cart.items.count() > 0:
                    print(f"✅ Found another active cart with items: {user_cart.id}")
                    cart = user_cart
                else:
                    any_cart = Cart.objects.filter(user=request.user).order_by('-created_at').first()
                    if any_cart and any_cart.items.count() > 0:
                        print(f"✅ Found cart with items (reactivating): {any_cart.id}")
                        any_cart.is_active = True
                        any_cart.save()
                        cart = any_cart

            if cart.items.count() == 0 and request.session.get('cart_id'):
                session_cart_id = request.session.get('cart_id')
                session_cart = Cart.objects.filter(id=session_cart_id, is_active=True).first()
                if session_cart and session_cart.items.count() > 0:
                    print(f"✅ Found cart from session: {session_cart.id}")
                    cart = session_cart

        if cart.items.count() == 0:
            print("❌ Cart is empty after all attempts!")
            return Response(
                {'error': 'Cart is empty. Please add items before ordering.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"✅ Final cart: {cart.id} with {cart.items.count()} items")

        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request, 'cart': cart}
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        delivery_info, _ = DeliveryInfo.objects.get_or_create(cart=cart)

        delivery_data = {
            'address': data['delivery_address'],
            'city': data['delivery_city'],
            'state': data.get('delivery_state') or '',
            'postal_code': data.get('delivery_postal_code') or '',
            'delivery_date': data['delivery_date'],
            'delivery_time_slot': data.get('delivery_time_slot') or '',
            'special_instructions': data.get('special_instructions') or '',
            'delivery_fee': cart.delivery_cost or Decimal('0.00'),
        }

        from orders.models import create_order_from_cart
        order = create_order_from_cart(
            cart=cart,
            customer_data={
                'name': data['customer_name'],
                'email': data['customer_email'],
                'phone': data['customer_phone'],
            },
            delivery_data=delivery_data,
        )

        is_authenticated = False
        user = None

        try:
            if hasattr(request, 'user') and request.user:
                if request.user.is_authenticated:
                    is_authenticated = True
                    user = request.user
        except Exception:
            pass

        if is_authenticated and user:
            order.user = user
            order.status = 'pending'
            order.save()

            OrderHistory.objects.create(
                order=order,
                action='created',
                description=f"Order created by {user.email}",
                changed_by=user,
                old_value='',
                new_value='pending'
            )
            requires_auth = False
            message = "Order created successfully. Proceed to payment."
        else:
            order.status = 'pending'
            order.save()

            OrderHistory.objects.create(
                order=order,
                action='created',
                description="Guest order created",
                changed_by=None,
                old_value='',
                new_value='pending'
            )
            requires_auth = True
            message = "Order created successfully. Please login to complete payment."

        # ✅ Send branded HTML order confirmation email
        try:
            send_order_confirmation(order)
        except Exception as e:
            # Don't break order creation if email fails
            print(f"⚠️ Order confirmation email failed: {e}")

        response_serializer = OrderDetailSerializer(order)

        return Response({
            'message': message,
            'order': response_serializer.data,
            'requires_authentication': requires_auth,
            'order_id': order.id,
            'order_number': order.order_number,
        }, status=status.HTTP_201_CREATED)


class CancelOrderView(APIView):
    """
    PATCH /api/orders/<id>/cancel/
    Cancel an order.
    """
    permission_classes = [IsOrderOwnerOrAdmin]

    @swagger_auto_schema(
        operation_summary="Cancel Order",
        operation_description="Cancel an order that is not yet completed or already cancelled.",
        request_body=OrderCancelSerializer,
        responses={
            200: openapi.Response(description="Order cancelled successfully."),
            400: openapi.Response(description="Order cannot be cancelled."),
            401: openapi.Response(description="Authentication required."),
            403: openapi.Response(description="You do not have permission to cancel this order."),
        }
    )
    def patch(self, request, id):
        order = get_object_or_404(Order, id=id)
        self.check_object_permissions(request, order)

        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if order.status in ['completed', 'cancelled']:
            return Response({
                'error': f'Order cannot be cancelled. Current status: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        reason = serializer.validated_data.get('reason', '')
        order.update_status('cancelled', request.user if request.user.is_authenticated else None, reason)

        # ✅ Send branded cancellation email (handled inside send_order_status_update)
        try:
            send_order_status_update(order)
        except Exception as e:
            print(f"⚠️ Cancellation email failed: {e}")

        return Response({
            'message': 'Order cancelled successfully.',
            'order': OrderDetailSerializer(order).data
        })


class CheckoutOrderView(APIView):
    """
    GET /api/orders/<id>/checkout/
    Check if user can proceed to payment.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        order = get_object_or_404(Order, id=id)

        is_authenticated = False
        user = None

        try:
            if hasattr(request, 'user') and request.user:
                if request.user.is_authenticated:
                    is_authenticated = True
                    user = request.user
        except Exception:
            is_authenticated = False
            user = None

        if is_authenticated and user:
            if not order.user:
                order.user = user
                order.save()
                OrderHistory.objects.create(
                    order=order,
                    action='status_changed',
                    description=f"Guest order associated with user {user.email}",
                    changed_by=user,
                    old_value='guest',
                    new_value='authenticated'
                )

            if order.user != user and not user.is_staff:
                return Response({
                    'error': 'You do not have permission to view this order.'
                }, status=status.HTTP_403_FORBIDDEN)

            if order.status == 'cancelled':
                return Response({'error': 'This order has been cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

            if order.payment_status == 'paid':
                return Response({'error': 'This order has already been paid.'}, status=status.HTTP_400_BAD_REQUEST)

            delivery_info = None
            if hasattr(order, 'delivery') and order.delivery:
                delivery_info = {
                    'delivery_date': order.delivery.delivery_date,
                    'address': order.delivery.address,
                    'city': order.delivery.city,
                }

            return Response({
                'message': 'Ready for payment.',
                'can_proceed_to_payment': True,
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': str(order.total_amount),
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'delivery': delivery_info,
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                'message': 'Authentication required to proceed with payment.',
                'requires_authentication': True,
                'order_id': order.id,
                'order_number': order.order_number,
            }, status=status.HTTP_401_UNAUTHORIZED)


class TrackOrderView(APIView):
    """
    GET /api/orders/<id>/track/
    Track an order - public access.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Track Order",
        operation_description="Get the current status and timeline of an order. No authentication required.",
        responses={
            200: openapi.Response(description="Order tracking details."),
            404: openapi.Response(description="Order not found."),
        }
    )
    def get(self, request, id):
        order = get_object_or_404(Order, id=id)

        data = {
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_color': order.get_status_display_color(),
            'created_at': order.created_at,
            'estimated_ready_date': None,
            'timeline': []
        }

        for history in order.history.all().order_by('timestamp')[:10]:
            data['timeline'].append({
                'action': history.get_action_display(),
                'description': history.description,
                'timestamp': history.timestamp
            })

        return Response(data)


class TrackOrderByNumberView(APIView):
    """
    GET /api/orders/track/?order_number=ORD-20260508-1D973DB8
    Public — no auth required.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        order_number = request.query_params.get('order_number')
        if not order_number:
            return Response(
                {'error': 'order_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(Order, order_number=order_number)

        data = {
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_color': order.get_status_display_color(),
            'created_at': order.created_at,
            'estimated_ready_date': None,
            'timeline': []
        }

        for history in order.history.all().order_by('timestamp')[:10]:
            data['timeline'].append({
                'action': history.get_action_display(),
                'description': history.description,
                'timestamp': history.timestamp
            })

        return Response(data)


# ============================================================================
# ADMIN ONLY VIEWS
# ============================================================================

class AdminOrderUpdateView(APIView):
    """
    PUT /api/admin/orders/<id>/status/
    Update order status - Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Update Order Status (Admin)",
        operation_description="Update the status of an order. Admin only.",
        request_body=OrderStatusUpdateSerializer,
        responses={
            200: openapi.Response(description="Order status updated."),
            400: openapi.Response(description="Validation error."),
            401: openapi.Response(description="Authentication required."),
            403: openapi.Response(description="Admin access required."),
        }
    )
    def put(self, request, id):
        order = get_object_or_404(Order, id=id)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        new_status = data['status']
        reason = data.get('reason', '')
        notify = data.get('notify_customer', True)

        order.update_status(new_status, request.user, reason)

        # ✅ Send branded HTML status update email (if notify flag is true)
        if notify:
            try:
                send_order_status_update(order)
            except Exception as e:
                print(f"⚠️ Status update email failed: {e}")

        return Response({
            'message': f'Order status updated to {order.get_status_display()}.',
            'order': OrderDetailSerializer(order).data
        })


class AdminPaymentUpdateView(APIView):
    """
    PUT /api/admin/orders/<id>/payment/
    Update payment status - Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Update Payment Status (Admin)",
        operation_description="Update the payment status of an order. Admin only.",
        request_body=OrderPaymentUpdateSerializer,
        responses={
            200: openapi.Response(description="Payment status updated."),
            400: openapi.Response(description="Validation error."),
            401: openapi.Response(description="Authentication required."),
            403: openapi.Response(description="Admin access required."),
        }
    )
    def put(self, request, id):
        order = get_object_or_404(Order, id=id)

        serializer = OrderPaymentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        old_status = order.payment_status
        order.payment_status = data['payment_status']

        if data.get('transaction_id'):
            order.paystack_transaction_id = data['transaction_id']

        if data.get('paystack_reference'):
            order.paystack_reference = data['paystack_reference']

        if data['payment_status'] == 'paid' and not order.payment_date:
            order.payment_date = now()

        order.save()

        OrderHistory.objects.create(
            order=order,
            action='payment_received' if data['payment_status'] == 'paid' else 'status_changed',
            description=f"Payment status changed from {old_status} to {data['payment_status']}",
            changed_by=request.user,
            old_value=old_status,
            new_value=data['payment_status']
        )

        # ✅ Send payment confirmed email when payment becomes 'paid'
        if data['payment_status'] == 'paid':
            try:
                from orders.emails import send_payment_confirmed
                send_payment_confirmed(order)
            except Exception as e:
                print(f"⚠️ Payment confirmed email failed: {e}")

        return Response({
            'message': f'Payment status updated to {order.get_payment_status_display()}.',
            'order': OrderDetailSerializer(order).data
        })


class AdminOrderStatsView(APIView):
    """
    GET /api/admin/orders/stats/
    Order statistics - Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Order Statistics (Admin)",
        operation_description="Get a breakdown of order and revenue statistics. Admin only.",
        responses={
            200: openapi.Response(description="Order statistics."),
            401: openapi.Response(description="Authentication required."),
            403: openapi.Response(description="Admin access required."),
        }
    )
    def get(self, request):
        from django.db.models import Count, Sum
        from datetime import timedelta

        today = now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        stats = {
            'total_orders': Order.objects.count(),
            'total_revenue': Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0,
            'orders_today': Order.objects.filter(created_at__date=today).count(),
            'revenue_today': Order.objects.filter(created_at__date=today).aggregate(
                total=Sum('total_amount'))['total'] or 0,
            'orders_this_week': Order.objects.filter(created_at__date__gte=week_ago).count(),
            'orders_this_month': Order.objects.filter(created_at__date__gte=month_ago).count(),
            'status_breakdown': Order.objects.values('status').annotate(count=Count('id')),
            'payment_status_breakdown': Order.objects.values('payment_status').annotate(count=Count('id')),
        }

        return Response(stats)