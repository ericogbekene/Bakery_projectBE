from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal

from orders.models import Order, OrderHistory, OrderPayment
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
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        cart = serializer.context['cart']

        delivery_info, _ = DeliveryInfo.objects.get_or_create(cart=cart)

        delivery_data = {
            'address': data['delivery_address'],
            'city': data['delivery_city'],
            'state': data.get('delivery_state', ''),
            'postal_code': data.get('delivery_postal_code', ''),
            'delivery_date': data['delivery_date'],
            'delivery_time_slot': data.get('delivery_time_slot', ''),
            'special_instructions': data.get('special_instructions', ''),
            'delivery_fee': cart.delivery_cost,
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

        try:
            send_mail(
                subject=f"Order Confirmation - {order.order_number}",
                message=(
                    f"Dear {order.customer_name},\n\n"
                    f"Thank you for your order! Here are your order details:\n"
                    f"Order Number: {order.order_number}\n"
                    f"Total Amount: ₦{order.total_amount:,.2f}\n"
                    f"Delivery Date: {order.delivery.delivery_date}\n\n"
                    f"We will notify you once your order is confirmed.\n\n"
                    f"Thank you for choosing us!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer_email],
                fail_silently=True,
            )
        except Exception:
            pass

        response_serializer = OrderDetailSerializer(order)
        return Response({
            'message': 'Order created successfully.',
            'order': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class CancelOrderView(APIView):
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

        return Response({
            'message': 'Order cancelled successfully.',
            'order': OrderDetailSerializer(order).data
        })


class TrackOrderView(APIView):
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

        if notify:
            try:
                send_mail(
                    subject=f"Order Update - {order.order_number}",
                    message=(
                        f"Dear {order.customer_name},\n\n"
                        f"Your order #{order.order_number} status has been updated to: "
                        f"{order.get_status_display()}.\n\n"
                        f"Thank you for your patience!"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer_email],
                    fail_silently=True,
                )
            except Exception:
                pass

        return Response({
            'message': f'Order status updated to {order.get_status_display()}.',
            'order': OrderDetailSerializer(order).data
        })


class AdminPaymentUpdateView(APIView):
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
            order.flutterwave_transaction_id = data['transaction_id']

        if data.get('flutterwave_reference'):
            order.flutterwave_reference = data['flutterwave_reference']

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

        return Response({
            'message': f'Payment status updated to {order.get_payment_status_display()}.',
            'order': OrderDetailSerializer(order).data
        })


class AdminOrderStatsView(APIView):
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