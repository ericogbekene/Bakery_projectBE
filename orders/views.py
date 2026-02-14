# from django.shortcuts import get_object_or_404
# from django.http import JsonResponse
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from django.utils.timezone import now
# from django.db import transaction
# from decimal import Decimal
# import uuid

# from products.models import Product
# from .models import (
#     Cart, CartItem, Order, OrderItem, OrderHistory, OrderPayment,
#     CakeCustomizationOption, CakeSizePrice, CakeFlavorPrice
# )
# from .utils import get_or_create_cart, clear_cart
# from .serializers import (
#     CartItemDetailSerializer, CartSummarySerializer,
#     CartItemCreateUpdateSerializer
# )


# # ============================================================================
# # ORDER CREATION & CHECKOUT VIEWS
# # ============================================================================

# class CheckoutAPIView(APIView):
#     """
#     Checkout page - Get cart and calculate taxes/fees.
    
#     GET /api/checkout/
    
#     Returns:
#     {
#         "success": true,
#         "cart": {...},
#         "tax_rate": 0.1,
#         "delivery_fee": 1000.00,
#         "estimated_total": 53250.00
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request):
#         try:
#             cart = get_or_create_cart(request)
            
#             if not cart.items.exists():
#                 return Response({
#                     'success': False,
#                     'error': 'Cart is empty'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Calculate taxes and fees
#             TAX_RATE = Decimal('0.10')  # 10% tax
#             DELIVERY_FEE = Decimal('1000.00')  # ₦1,000
            
#             subtotal = cart.total_price
#             tax_amount = (subtotal * TAX_RATE).quantize(Decimal('0.01'))
#             estimated_total = subtotal + tax_amount + DELIVERY_FEE
            
#             return Response({
#                 'success': True,
#                 'cart': {
#                     'id': cart.id,
#                     'items': CartItemDetailSerializer(cart.items.all(), many=True).data,
#                     'subtotal': str(subtotal),
#                     'item_count': cart.item_count,
#                 },
#                 'tax_rate': float(TAX_RATE),
#                 'tax_amount': str(tax_amount),
#                 'delivery_fee': str(DELIVERY_FEE),
#                 'estimated_total': str(estimated_total),
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


# class CreateOrderAPIView(APIView):
#     """
#     Create order from cart.
    
#     POST /api/orders/create/
    
#     Body:
#     {
#         "delivery_address": "123 Main St, Apt 4B",
#         "delivery_city": "Abuja",
#         "delivery_phone": "+234 701 234 5678",
#         "delivery_date": "2024-02-15",
#         "delivery_time": "14:00",  # optional
#         "special_instructions": "Ring doorbell twice",
#         "discount_code": "SAVE10"  # optional
#     }
    
#     Response:
#     {
#         "success": true,
#         "order": {
#             "order_number": "ORD-20240129-ABC12345",
#             "total_amount": "53250.00",
#             "status": "pending",
#             "payment_status": "pending"
#         }
#     }
#     """
#     permission_classes = [AllowAny]
    
#     @transaction.atomic
#     def post(self, request):
#         try:
#             # Get cart
#             cart = get_or_create_cart(request)
            
#             if not cart.items.exists():
#                 return Response({
#                     'success': False,
#                     'error': 'Cart is empty'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Validate required fields
#             required_fields = [
#                 'delivery_address',
#                 'delivery_city',
#                 'delivery_phone',
#                 'delivery_date'
#             ]
            
#             for field in required_fields:
#                 if not request.data.get(field):
#                     return Response({
#                         'success': False,
#                         'error': f'{field} is required'
#                     }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Calculate totals
#             TAX_RATE = Decimal('0.10')
#             DELIVERY_FEE = Decimal('1000.00')
            
#             subtotal = cart.total_price
#             tax_amount = (subtotal * TAX_RATE).quantize(Decimal('0.01'))
            
#             # Handle discount
#             discount_amount = Decimal('0.00')
#             discount_code = request.data.get('discount_code', '')
#             # TODO: Implement discount code validation
            
#             total_amount = subtotal + tax_amount + DELIVERY_FEE - discount_amount
            
#             # Create order
#             order = Order.objects.create(
#                 user=request.user if request.user.is_authenticated else None,
#                 guest_email=request.data.get('guest_email', ''),
#                 guest_phone=request.data.get('guest_phone', ''),
#                 cart=cart,
#                 delivery_address=request.data['delivery_address'],
#                 delivery_city=request.data['delivery_city'],
#                 delivery_phone=request.data['delivery_phone'],
#                 delivery_date=request.data['delivery_date'],
#                 delivery_time=request.data.get('delivery_time'),
#                 special_instructions=request.data.get('special_instructions', ''),
#                 subtotal=subtotal,
#                 tax_amount=tax_amount,
#                 delivery_fee=DELIVERY_FEE,
#                 discount_amount=discount_amount,
#                 discount_code=discount_code,
#                 total_amount=total_amount,
#                 status='pending',
#                 payment_status='pending'
#             )
            
#             # Create order items from cart items
#             for cart_item in cart.items.all():
#                 OrderItem.objects.create(
#                     order=order,
#                     product=cart_item.product,
#                     quantity=cart_item.quantity,
#                     flavour_1=cart_item.flavour_1,
#                     flavour_2=cart_item.flavour_2,
#                     size=cart_item.size,
#                     colours=cart_item.colours,
#                     cake_topper=cart_item.cake_topper,
#                     candle=cart_item.candle,
#                     birthday_card=cart_item.birthday_card,
#                     chocolate=cart_item.chocolate,
#                     wine=cart_item.wine,
#                     whiskey_200ml=cart_item.whiskey_200ml,
#                     additional_notes=cart_item.additional_notes,
#                     base_price=cart_item.base_price,
#                     customization_cost=cart_item.customization_cost,
#                     unit_price=cart_item.unit_price
#                 )
            
#             # Add history entry
#             OrderHistory.objects.create(
#                 order=order,
#                 action='created',
#                 description='Order created',
#                 changed_by=request.user if request.user.is_authenticated else None
#             )
            
#             # Clear/deactivate cart
#             cart.is_active = False
#             cart.save()
            
#             return Response({
#                 'success': True,
#                 'order': {
#                     'order_number': order.order_number,
#                     'id': order.id,
#                     'total_amount': str(order.total_amount),
#                     'status': order.status,
#                     'payment_status': order.payment_status,
#                     'created_at': order.created_at.isoformat(),
#                 },
#                 'message': f'Order {order.order_number} created successfully'
#             }, status=status.HTTP_201_CREATED)
        
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


# # ============================================================================
# # PAYMENT VIEWS
# # ============================================================================

# class InitiatePaymentAPIView(APIView):
#     """
#     Initiate payment for an order.
    
#     POST /api/orders/{order_number}/pay/
    
#     Body:
#     {
#         "payment_method": "stripe",  // or "card", "bank_transfer", "paypal", "cash"
#         "payment_token": "tok_visa"   // token from payment gateway
#     }
    
#     Response:
#     {
#         "success": true,
#         "payment": {
#             "transaction_id": "ch_1234567890",
#             "status": "paid",
#             "amount": "53250.00"
#         }
#     }
#     """
#     permission_classes = [AllowAny]
    
#     @transaction.atomic
#     def post(self, request, order_number):
#         try:
#             order = Order.objects.get(order_number=order_number)
            
#             # Verify order ownership
#             if order.user and order.user != request.user:
#                 if not request.user.is_staff:
#                     return Response({
#                         'success': False,
#                         'error': 'Unauthorized'
#                     }, status=status.HTTP_403_FORBIDDEN)
            
#             payment_method = request.data.get('payment_method')
            
#             if not payment_method:
#                 return Response({
#                     'success': False,
#                     'error': 'payment_method is required'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # TODO: Integrate with payment gateway
#             # For now, create transaction record
            
#             transaction_id = f"{payment_method.upper()}-{str(uuid.uuid4())[:12].upper()}"
            
#             # Create payment record
#             payment = OrderPayment.objects.create(
#                 order=order,
#                 amount=order.total_amount,
#                 payment_method=payment_method,
#                 transaction_id=transaction_id,
#                 status='paid',  # In production, this would depend on gateway response
#                 processed_at=now()
#             )
            
#             # Update order
#             order.payment_status = 'paid'
#             order.payment_date = now()
#             order.payment_transaction_id = transaction_id
#             order.save()
            
#             # Add history entry
#             OrderHistory.objects.create(
#                 order=order,
#                 action='payment_received',
#                 description=f'Payment received via {payment_method}',
#                 changed_by=request.user if request.user.is_authenticated else None,
#                 old_value='pending',
#                 new_value='paid'
#             )
            
#             return Response({
#                 'success': True,
#                 'payment': {
#                     'transaction_id': payment.transaction_id,
#                     'amount': str(payment.amount),
#                     'status': payment.status,
#                     'payment_method': payment.payment_method,
#                     'created_at': payment.created_at.isoformat(),
#                 },
#                 'order': {
#                     'order_number': order.order_number,
#                     'payment_status': order.payment_status,
#                     'status': order.status,
#                 }
#             }, status=status.HTTP_200_OK)
        
#         except Order.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Order not found'
#             }, status=status.HTTP_404_NOT_FOUND)
        
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


# # ============================================================================
# # ORDER MANAGEMENT VIEWS
# # ============================================================================

# class OrderDetailAPIView(APIView):
#     """
#     Get order details.
    
#     GET /api/orders/{order_number}/
    
#     Response:
#     {
#         "success": true,
#         "order": {
#             "order_number": "ORD-20240129-ABC12345",
#             "customer": "John Doe",
#             "status": "confirmed",
#             "payment_status": "paid",
#             "items": [...],
#             "total_amount": "53250.00",
#             "delivery_address": "...",
#             "delivery_date": "2024-02-15"
#         }
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request, order_number):
#         try:
#             order = Order.objects.get(order_number=order_number)
            
#             # Verify access
#             if order.user and order.user != request.user:
#                 if not request.user.is_staff:
#                     return Response({
#                         'success': False,
#                         'error': 'Unauthorized'
#                     }, status=status.HTTP_403_FORBIDDEN)
            
#             # Get items
#             items = []
#             for item in order.items.all():
#                 items.append({
#                     'id': item.id,
#                     'product': item.product.name if item.product else 'Unknown',
#                     'quantity': item.quantity,
#                     'flavours': f"{item.flavour_1}" + (f" + {item.flavour_2}" if item.flavour_2 else ""),
#                     'size': item.size,
#                     'customizations': item.get_addons_summary(),
#                     'unit_price': str(item.unit_price),
#                     'item_total': str(item.item_total),
#                     'special_notes': item.additional_notes,
#                 })
            
#             # Get payment info
#             payments = []
#             for payment in order.payments.all():
#                 payments.append({
#                     'transaction_id': payment.transaction_id,
#                     'amount': str(payment.amount),
#                     'payment_method': payment.payment_method,
#                     'status': payment.status,
#                     'created_at': payment.created_at.isoformat(),
#                 })
            
#             # Get history
#             history = []
#             for h in order.history.all():
#                 history.append({
#                     'action': h.get_action_display(),
#                     'description': h.description,
#                     'changed_by': h.changed_by.username if h.changed_by else 'System',
#                     'timestamp': h.timestamp.isoformat(),
#                 })
            
#             return Response({
#                 'success': True,
#                 'order': {
#                     'order_number': order.order_number,
#                     'customer_name': order.customer_name,
#                     'customer_email': order.customer_email,
#                     'customer_phone': order.customer_phone,
#                     'status': order.status,
#                     'status_display': order.get_status_display(),
#                     'payment_status': order.payment_status,
#                     'payment_status_display': order.get_payment_status_display(),
#                     'payment_method': order.payment_method,
#                     'items': items,
#                     'delivery': {
#                         'address': order.delivery_address,
#                         'city': order.delivery_city,
#                         'phone': order.delivery_phone,
#                         'date': order.delivery_date.isoformat(),
#                         'time': order.delivery_time.isoformat() if order.delivery_time else None,
#                         'special_instructions': order.special_instructions,
#                     },
#                     'pricing': {
#                         'subtotal': str(order.subtotal),
#                         'tax': str(order.tax_amount),
#                         'delivery_fee': str(order.delivery_fee),
#                         'discount': str(order.discount_amount),
#                         'discount_code': order.discount_code,
#                         'total': str(order.total_amount),
#                     },
#                     'timeline': {
#                         'created': order.created_at.isoformat(),
#                         'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
#                         'completed': order.completed_at.isoformat() if order.completed_at else None,
#                     },
#                     'payments': payments,
#                     'history': history,
#                 }
#             }, status=status.HTTP_200_OK)
        
#         except Order.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Order not found'
#             }, status=status.HTTP_404_NOT_FOUND)


# class OrderListAPIView(APIView):
#     """
#     List customer's orders.
    
#     GET /api/orders/
    
#     Response:
#     {
#         "success": true,
#         "orders": [
#             {
#                 "order_number": "ORD-20240129-ABC12345",
#                 "status": "confirmed",
#                 "total_amount": "53250.00",
#                 "created_at": "2024-01-29T10:00:00Z"
#             }
#         ]
#     }
#     """
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         try:
#             orders = Order.objects.filter(user=request.user).order_by('-created_at')
            
#             orders_data = []
#             for order in orders:
#                 orders_data.append({
#                     'order_number': order.order_number,
#                     'status': order.status,
#                     'status_display': order.get_status_display(),
#                     'payment_status': order.payment_status,
#                     'total_amount': str(order.total_amount),
#                     'delivery_date': order.delivery_date.isoformat(),
#                     'created_at': order.created_at.isoformat(),
#                     'item_count': order.items.count(),
#                 })
            
#             return Response({
#                 'success': True,
#                 'orders': orders_data,
#                 'count': len(orders_data),
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


# class ConfirmOrderAPIView(APIView):
#     """
#     Confirm order (admin only).
    
#     POST /api/orders/{order_number}/confirm/
    
#     Response:
#     {
#         "success": true,
#         "order": {
#             "order_number": "ORD-20240129-ABC12345",
#             "status": "confirmed",
#             "confirmed_at": "2024-01-29T11:00:00Z"
#         }
#     }
#     """
#     permission_classes = [IsAuthenticated]
    
#     @transaction.atomic
#     def post(self, request, order_number):
#         try:
#             if not request.user.is_staff:
#                 return Response({
#                     'success': False,
#                     'error': 'Only staff can confirm orders'
#                 }, status=status.HTTP_403_FORBIDDEN)
            
#             order = Order.objects.get(order_number=order_number)
            
#             if order.status != 'pending':
#                 return Response({
#                     'success': False,
#                     'error': f'Cannot confirm order in {order.status} status'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             order.status = 'confirmed'
#             order.confirmed_at = now()
#             order.save()
            
#             OrderHistory.objects.create(
#                 order=order,
#                 action='confirmed',
#                 description='Order confirmed by admin',
#                 changed_by=request.user,
#                 old_value='pending',
#                 new_value='confirmed'
#             )
            
#             return Response({
#                 'success': True,
#                 'order': {
#                     'order_number': order.order_number,
#                     'status': order.status,
#                     'confirmed_at': order.confirmed_at.isoformat(),
#                 }
#             }, status=status.HTTP_200_OK)
        
#         except Order.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Order not found'
#             }, status=status.HTTP_404_NOT_FOUND)


# class UpdateOrderStatusAPIView(APIView):
#     """
#     Update order status (admin only).
    
#     PUT /api/orders/{order_number}/status/
    
#     Body:
#     {
#         "status": "processing",  // or "ready", "completed", "cancelled"
#         "notes": "Order is being prepared"
#     }
#     """
#     permission_classes = [IsAuthenticated]
    
#     @transaction.atomic
#     def put(self, request, order_number):
#         try:
#             if not request.user.is_staff:
#                 return Response({
#                     'success': False,
#                     'error': 'Only staff can update order status'
#                 }, status=status.HTTP_403_FORBIDDEN)
            
#             order = Order.objects.get(order_number=order_number)
#             new_status = request.data.get('status')
#             notes = request.data.get('notes', '')
            
#             if not new_status:
#                 return Response({
#                     'success': False,
#                     'error': 'status is required'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Validate status
#             valid_statuses = ['pending', 'confirmed', 'processing', 'ready', 'completed', 'cancelled']
#             if new_status not in valid_statuses:
#                 return Response({
#                     'success': False,
#                     'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             old_status = order.status
#             order.status = new_status
            
#             if new_status == 'completed':
#                 order.completed_at = now()
#             elif new_status == 'cancelled':
#                 order.cancelled_at = now()
#                 order.cancellation_reason = notes
            
#             order.save()
            
#             OrderHistory.objects.create(
#                 order=order,
#                 action=new_status,
#                 description=notes or f'Status changed to {new_status}',
#                 changed_by=request.user,
#                 old_value=old_status,
#                 new_value=new_status
#             )
            
#             return Response({
#                 'success': True,
#                 'order': {
#                     'order_number': order.order_number,
#                     'status': order.status,
#                     'updated_at': order.updated_at.isoformat(),
#                 }
#             }, status=status.HTTP_200_OK)
        
#         except Order.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Order not found'
#             }, status=status.HTTP_404_NOT_FOUND)


# class CancelOrderAPIView(APIView):
#     """
#     Cancel order.
    
#     POST /api/orders/{order_number}/cancel/
    
#     Body:
#     {
#         "reason": "Changed my mind"
#     }
#     """
#     permission_classes = [AllowAny]
    
#     @transaction.atomic
#     def post(self, request, order_number):
#         try:
#             order = Order.objects.get(order_number=order_number)
            
#             # Verify access
#             if order.user and order.user != request.user:
#                 if not request.user.is_staff:
#                     return Response({
#                         'success': False,
#                         'error': 'Unauthorized'
#                     }, status=status.HTTP_403_FORBIDDEN)
            
#             if order.status == 'cancelled':
#                 return Response({
#                     'success': False,
#                     'error': 'Order is already cancelled'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if order.status == 'completed':
#                 return Response({
#                     'success': False,
#                     'error': 'Cannot cancel completed order'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             reason = request.data.get('reason', 'No reason provided')
            
#             order.status = 'cancelled'
#             order.cancelled_at = now()
#             order.cancellation_reason = reason
#             order.save()
            
#             OrderHistory.objects.create(
#                 order=order,
#                 action='cancelled',
#                 description=reason,
#                 changed_by=request.user if request.user.is_authenticated else None
#             )
            
#             return Response({
#                 'success': True,
#                 'order': {
#                     'order_number': order.order_number,
#                     'status': order.status,
#                     'cancelled_at': order.cancelled_at.isoformat(),
#                 }
#             }, status=status.HTTP_200_OK)
        
#         except Order.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Order not found'
#             }, status=status.HTTP_404_NOT_FOUND)