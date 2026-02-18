from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal

from cart.models import Cart, CartItem, DeliveryInfo
from products.models import Product
from cart.utils import (
    get_or_create_cart, get_cart_item_count,
    clear_cart, remove_cart_item
)
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, PriceCalculationSerializer,
    DeliveryInfoSerializer, GuestCartMergeSerializer
)


class CartDetailView(APIView):
    """
    GET /api/cart/ - Get current cart
    DELETE /api/cart/ - Clear entire cart
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get current cart with all items."""
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def delete(self, request):
        """Clear all items from cart."""
        cart = clear_cart(request)
        return Response({
            'message': 'Cart cleared successfully.',
            'cart': CartSerializer(cart).data
        })


class AddToCartView(APIView):
    """
    POST /api/cart/add/ - Add item to cart
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        product = serializer.context['product']
        
        # Get or create cart
        cart = get_or_create_cart(request)
        
        # Check if identical item exists
        existing_item = CartItem.objects.filter(
            cart=cart,
            product=product,
            flavour_1=data.get('flavour_1', ''),
            flavour_2=data.get('flavour_2', ''),
            size=data.get('size', ''),
            colours=data.get('colours', ''),
            cake_topper=data.get('cake_topper', 0),
            candle=data.get('candle', 0),
            birthday_card=data.get('birthday_card', 0),
            chocolate=data.get('chocolate', 0),
            wine=data.get('wine', 0),
            whiskey_200ml=data.get('whiskey_200ml', 0),
            additional_notes=data.get('additional_notes', '')
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += data.get('quantity', 1)
            existing_item.save()
            item = existing_item
            message = f"Updated quantity of {product.name} in cart"
        else:
            # Create new cart item
            cart_item = CartItem(
                cart=cart,
                product=product,
                quantity=data.get('quantity', 1),
                flavour_1=data.get('flavour_1', ''),
                flavour_2=data.get('flavour_2', ''),
                size=data.get('size', ''),
                colours=data.get('colours', ''),
                cake_topper=data.get('cake_topper', 0),
                candle=data.get('candle', 0),
                birthday_card=data.get('birthday_card', 0),
                chocolate=data.get('chocolate', 0),
                wine=data.get('wine', 0),
                whiskey_200ml=data.get('whiskey_200ml', 0),
                additional_notes=data.get('additional_notes', ''),
                base_price=product.price  # Snapshot of product price
            )
            # Calculate and set customization cost
            cart_item.customization_cost = cart_item.calculate_addons_cost()
            cart_item.save()
            item = cart_item
            message = f"Added {product.name} to cart"
        
        return Response({
            'message': message,
            'cart_item': CartItemSerializer(item).data,
            'cart_item_count': get_cart_item_count(request)
        }, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    """
    PUT /api/cart/items/<id>/ - Update cart item
    DELETE /api/cart/items/<id>/ - Remove cart item
    """
    permission_classes = [permissions.AllowAny]
    
    def get_object(self, request, item_id):
        cart = get_or_create_cart(request)
        return get_object_or_404(CartItem, id=item_id, cart=cart)
    
    def put(self, request, item_id):
        cart_item = self.get_object(request, item_id)
        
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        action = data.get('action')
        quantity = data.get('quantity', 1)
        
        if action == 'set':
            cart_item.quantity = quantity
        elif action == 'increase':
            cart_item.quantity += quantity
        elif action == 'decrease':
            if cart_item.quantity <= quantity:
                cart_item.delete()
                return Response({
                    'message': 'Item removed from cart.',
                    'cart_item_count': get_cart_item_count(request)
                })
            cart_item.quantity -= quantity
        
        cart_item.save()
        
        return Response({
            'message': 'Cart item updated successfully.',
            'cart_item': CartItemSerializer(cart_item).data,
            'cart_item_count': get_cart_item_count(request)
        })
    
    def delete(self, request, item_id):
        cart_item = self.get_object(request, item_id)
        product_name = cart_item.product.name
        cart_item.delete()
        
        return Response({
            'message': f'{product_name} removed from cart.',
            'cart_item_count': get_cart_item_count(request)
        })


class CalculatePriceView(APIView):
    """
    POST /api/cart/calculate-price/ - Real-time price calculation
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PriceCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        product = serializer.context['product']
        
        # Create a temporary cart item for calculation
        temp_item = CartItem(
            product=product,
            base_price=product.price,
            flavour_1=data.get('flavour_1', ''),
            flavour_2=data.get('flavour_2', ''),
            size=data.get('size', ''),
            cake_topper=data.get('cake_topper', 0),
            candle=data.get('candle', 0),
            birthday_card=data.get('birthday_card', 0),
            chocolate=data.get('chocolate', 0),
            wine=data.get('wine', 0),
            whiskey_200ml=data.get('whiskey_200ml', 0)
        )
        
        # Calculate prices
        unit_price = temp_item.calculate_total_price()
        addons_cost = temp_item.calculate_addons_cost()
        
        # Get multiplier values
        size_multiplier = temp_item.get_size_multiplier()
        flavor_multiplier = temp_item.get_flavor_multiplier()
        
        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'design_price': str(product.price),
            'size_multiplier': str(size_multiplier),
            'flavor_multiplier': str(flavor_multiplier),
            'cake_base_price': str(product.price * size_multiplier * flavor_multiplier),
            'addons_cost': str(addons_cost),
            'unit_price': str(unit_price),
            'formatted_price': f"₦{unit_price:,.2f}"
        })


class CartItemCountView(APIView):
    """
    GET /api/cart/count/ - Get total number of items in cart
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        count = get_cart_item_count(request)
        return Response({'count': count})


class CartSummaryView(APIView):
    """
    GET /api/cart/summary/ - Get cart summary with breakdown
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        cart = get_or_create_cart(request)
        items_data = []
        
        for item in cart.items.all():
            items_data.append({
                'id': item.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_item_price),
                'customization_summary': item.get_customization_summary(),
                'addons_breakdown': item.get_addons_breakdown()
            })
        
        return Response({
            'cart_id': cart.id,
            'item_count': cart.item_count,
            'subtotal': str(cart.subtotal),
            'delivery_cost': str(cart.delivery_cost),
            'grand_total': str(cart.grand_total),
            'items': items_data
        })


# ============================================================================
# DELIVERY INFO VIEWS
# ============================================================================

class DeliveryInfoView(APIView):
    """
    GET /api/cart/delivery/ - Get delivery info
    POST /api/cart/delivery/ - Add/update delivery info
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        cart = get_or_create_cart(request)
        
        try:
            delivery_info = cart.delivery_info
            serializer = DeliveryInfoSerializer(delivery_info)
            return Response(serializer.data)
        except DeliveryInfo.DoesNotExist:
            return Response({
                'message': 'No delivery information found.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        cart = get_or_create_cart(request)
        
        # Get or create delivery info
        delivery_info, created = DeliveryInfo.objects.get_or_create(cart=cart)
        
        serializer = DeliveryInfoSerializer(
            delivery_info, 
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # TODO: Calculate delivery fee based on zone
        # This will be implemented when delivery app is ready
        
        return Response({
            'message': 'Delivery information saved successfully.',
            'delivery_info': serializer.data
        })


# ============================================================================
# GUEST CART MERGING (for when user logs in)
# ============================================================================

class MergeGuestCartView(APIView):
    """
    POST /api/cart/merge/ - Merge guest cart with user cart on login
    Requires authentication
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = GuestCartMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_key = serializer.validated_data['session_key']
        
        # Get guest cart
        try:
            guest_cart = Cart.objects.get(
                session_key=session_key,
                is_active=True,
                user__isnull=True
            )
        except Cart.DoesNotExist:
            return Response({
                'message': 'No guest cart found to merge.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create user cart
        user_cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'session_key': None}
        )
        
        # Merge carts using existing utility function
        from cart.utils import merge_carts
        merged_cart = merge_carts(user_cart, guest_cart)
        
        return Response({
            'message': 'Carts merged successfully.',
            'cart': CartSerializer(merged_cart).data
        })