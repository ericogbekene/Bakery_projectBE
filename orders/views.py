from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.timezone import now
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
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user and request.user.is_staff:
            return True
        
        # Order owner (user or guest session) can view
        if obj.user and obj.user == request.user:
            return True
        
        # Guest checkout - check session
        if not obj.user and request.session.session_key:
            # This would need session tracking - implement if needed
            pass
        
        return False


class OrderListView(generics.ListAPIView):
    """
    GET /api/orders/
    
    List orders for the current user.
    - Authenticated users: see their own orders
    - Admin users: see all orders (with filters)
    - Guest users: see orders from their session (if implemented)
    """
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all orders
        if user.is_staff:
            queryset = Order.objects.all()
            
            # Apply filters
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
        
        # Regular authenticated users see their own orders
        if user.is_authenticated:
            return Order.objects.filter(user=user).order_by('-created_at')
        
        # Guest users - return empty for now
        # Could implement session-based order lookup
        return Order.objects.none()


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
    
    Create a new order from the current cart.
    """
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        cart = serializer.context['cart']
        
        # Get or create delivery info from cart
        delivery_info, _ = DeliveryInfo.objects.get_or_create(cart=cart)
        
        # Prepare delivery data
        delivery_data = {
            'address': data['delivery_address'],
            'city': data['delivery_city'],
            'state': data.get('delivery_state', ''),
            'postal_code': data.get('delivery_postal_code', ''),
            'delivery_date': data['delivery_date'],
            'delivery_time_slot': data.get('delivery_time_slot', ''),
            'special_instructions': data.get('special_instructions', ''),
            'delivery_fee': cart.delivery_cost,  # Will be calculated by delivery app
        }
        
        # Create order using utility function
        from orders.models import create_order_from_cart
        order = create_order_from_cart(
            cart=cart,
            customer_data={
                'name': data['customer_name'],
                'email': data['customer_email'],
                'phone': data['customer_phone'],
            },
            delivery_data=delivery_data,
            payment_method=data.get('payment_method', '')
        )
        
        # Return order details
        response_serializer = OrderDetailSerializer(order)
        return Response({
            'message': 'Order created successfully.',
            'order': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class CancelOrderView(APIView):
    """
    PUT /api/orders/<id>/cancel/
    
    Cancel an order (if within cancellation window).
    """
    permission_classes = [IsOrderOwnerOrAdmin]
    
    def put(self, request, id):
        order = get_object_or_404(Order, id=id)
        self.check_object_permissions(request, order)
        
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if order can be cancelled
        if order.status in ['completed', 'cancelled']:
            return Response({
                'error': f'Order cannot be cancelled. Current status: {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order status
        reason = serializer.validated_data.get('reason', '')
        order.update_status('cancelled', request.user if request.user.is_authenticated else None, reason)
        
        return Response({
            'message': 'Order cancelled successfully.',
            'order': OrderDetailSerializer(order).data
        })


class TrackOrderView(APIView):
    """
    GET /api/orders/<id>/track/
    
    Track order status and timeline.
    Public endpoint - no authentication required (uses order number).
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, id):
        order = get_object_or_404(Order, id=id)
        
        # Basic info for tracking
        data = {
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_color': order.get_status_display_color(),
            'created_at': order.created_at,
            'estimated_ready_date': None,  # Calculate based on preparation_days
            'timeline': []
        }
        
        # Build timeline from history
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
    PUT /api/orders/admin/<id>/update-status/
    
    Update order status (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    
    def put(self, request, id):
        order = get_object_or_404(Order, id=id)
        
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        new_status = data['status']
        reason = data.get('reason', '')
        notify = data.get('notify_customer', True)
        
        # Update status
        order.update_status(new_status, request.user, reason)
        
        # TODO: Send notification if notify=True
        
        return Response({
            'message': f'Order status updated to {order.get_status_display()}.',
            'order': OrderDetailSerializer(order).data
        })


class AdminPaymentUpdateView(APIView):
    """
    PUT /api/orders/admin/<id>/update-payment/
    
    Update payment status (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    
    def put(self, request, id):
        order = get_object_or_404(Order, id=id)
        
        serializer = OrderPaymentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Update payment status
        old_status = order.payment_status
        order.payment_status = data['payment_status']
        
        if data.get('transaction_id'):
            order.payment_transaction_id = data['transaction_id']
        
        if data['payment_status'] == 'paid' and not order.payment_date:
            order.payment_date = now()
        
        order.save()
        
        # Create history entry
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
    """
    GET /api/orders/admin/stats/
    
    Get order statistics (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        from django.db.models import Count, Sum
        from django.utils.timezone import now
        from datetime import timedelta
        
        today = now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_orders': Order.objects.count(),
            'total_revenue': Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0,
            'orders_today': Order.objects.filter(created_at__date=today).count(),
            'revenue_today': Order.objects.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0,
            'orders_this_week': Order.objects.filter(created_at__date__gte=week_ago).count(),
            'orders_this_month': Order.objects.filter(created_at__date__gte=month_ago).count(),
            'status_breakdown': Order.objects.values('status').annotate(count=Count('id')),
            'payment_status_breakdown': Order.objects.values('payment_status').annotate(count=Count('id')),
        }
        
        return Response(stats)