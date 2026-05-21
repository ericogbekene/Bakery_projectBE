from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal

from cart.models import Cart, CartItem, DeliveryInfo
from products.models import Product
from cart.utils import (
    get_or_create_cart,
    get_cart_item_count,
    clear_cart,
)
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, PriceCalculationSerializer,
    DeliveryInfoSerializer, GuestCartMergeSerializer
)
from delivery.models import DeliveryService


# ============================================================================
# CART VIEWS
# ============================================================================

class CartDetailView(APIView):
    """
    GET /api/cart/ - Get current cart
    DELETE /api/cart/ - Clear entire cart
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get Cart",
        operation_description="Get the current cart with all items, subtotal, delivery cost and grand total.",
        responses={
            200: openapi.Response(description="Cart retrieved successfully."),
        }
    )
    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Clear Cart",
        operation_description="Remove all items from the current cart.",
        responses={
            200: openapi.Response(description="Cart cleared successfully."),
        }
    )
    def delete(self, request):
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

    @swagger_auto_schema(
        operation_summary="Add Item to Cart",
        operation_description="Add a product to the cart with customization options. If identical item exists, quantity is updated.",
        request_body=AddToCartSerializer,
        responses={
            201: openapi.Response(description="Item added to cart."),
            200: openapi.Response(description="Existing item quantity updated."),
            400: openapi.Response(description="Validation error."),
        }
    )
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        product = serializer.context['product']

        cart = get_or_create_cart(request)

        # Check if identical item already exists in cart
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
            # Update quantity of existing item
            existing_item.quantity += data.get('quantity', 1)
            existing_item.save()
            return Response({
                'message': f"Updated quantity of {product.name} in cart.",
                'cart_item': CartItemSerializer(existing_item).data,
                'cart_item_count': get_cart_item_count(request)
            }, status=status.HTTP_200_OK)  # Fixed: 200 on update, not 201

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
                base_price=product.price
            )
            cart_item.customization_cost = cart_item.calculate_addons_cost()
            cart_item.save()

            return Response({
                'message': f"Added {product.name} to cart.",
                'cart_item': CartItemSerializer(cart_item).data,
                'cart_item_count': get_cart_item_count(request)
            }, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    """
    PATCH /api/cart/items/<id>/ - Update cart item quantity
    DELETE /api/cart/items/<id>/ - Remove cart item
    """
    permission_classes = [permissions.AllowAny]

    def get_object(self, request, item_id):
        cart = get_or_create_cart(request)
        return get_object_or_404(CartItem, id=item_id, cart=cart)

    @swagger_auto_schema(
        operation_summary="Update Cart Item",
        operation_description="Update the quantity of a cart item. Use action: 'set', 'increase', or 'decrease'.",
        request_body=UpdateCartItemSerializer,
        responses={
            200: openapi.Response(description="Cart item updated successfully."),
            400: openapi.Response(description="Validation error."),
            404: openapi.Response(description="Cart item not found."),
        }
    )
    def patch(self, request, item_id):  # Fixed: PUT -> PATCH for partial updates
        cart_item = self.get_object(request, item_id)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        action = data.get('action', 'set')
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

    @swagger_auto_schema(
        operation_summary="Remove Cart Item",
        operation_description="Remove a specific item from the cart.",
        responses={
            200: openapi.Response(description="Item removed from cart."),
            404: openapi.Response(description="Cart item not found."),
        }
    )
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

    @swagger_auto_schema(
        operation_summary="Calculate Price",
        operation_description="Calculate the price of a product with selected customizations in real time.",
        request_body=PriceCalculationSerializer,
        responses={
            200: openapi.Response(description="Price calculated successfully."),
            400: openapi.Response(description="Validation error."),
        }
    )
    def post(self, request):
        serializer = PriceCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        product = serializer.context['product']

        # Create a temporary (unsaved) cart item purely for calculation
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

        unit_price = temp_item.calculate_total_price()
        addons_cost = temp_item.calculate_addons_cost()
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

    @swagger_auto_schema(
        operation_summary="Get Cart Item Count",
        operation_description="Get the total number of items (sum of quantities) in the current cart.",
        responses={
            200: openapi.Response(description="Item count returned."),
        }
    )
    def get(self, request):
        count = get_cart_item_count(request)
        return Response({'count': count})


class CartSummaryView(APIView):
    """
    GET /api/cart/summary/ - Get cart summary with full breakdown
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get Cart Summary",
        operation_description="Get a full cart summary including all items, subtotal, delivery cost and grand total.",
        responses={
            200: openapi.Response(description="Cart summary returned."),
        }
    )
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
# DELIVERY INFO VIEW
# ============================================================================

class DeliveryInfoView(APIView):
    """
    GET /api/cart/delivery/ - Get delivery info
    POST /api/cart/delivery/ - Add/update delivery info
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get Delivery Info",
        operation_description="Get the delivery information saved for the current cart.",
        responses={
            200: openapi.Response(description="Delivery info returned."),
            404: openapi.Response(description="No delivery information found."),
        }
    )
    def get(self, request):
        cart = get_or_create_cart(request)

        try:
            delivery_info = cart.delivery_info
            serializer = DeliveryInfoSerializer(delivery_info)
            return Response(serializer.data)
        except DeliveryInfo.DoesNotExist:
            return Response(
                {'message': 'No delivery information found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_summary="Save Delivery Info",
        operation_description="Add or update delivery information for the current cart. Automatically calculates delivery fee based on city.",
        request_body=DeliveryInfoSerializer,
        responses={
            200: openapi.Response(description="Delivery information saved."),
            400: openapi.Response(description="Validation error."),
        }
    )
    def post(self, request):
        cart = get_or_create_cart(request)

        delivery_info, created = DeliveryInfo.objects.get_or_create(cart=cart)

        serializer = DeliveryInfoSerializer(
            delivery_info,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Calculate delivery fee — wrapped in try/except in case delivery app
        # has not been set up or DeliveryService method signature changes
        if delivery_info.city:
            try:
                result = DeliveryService.calculate_delivery_fee(
                    city=delivery_info.city,
                    order_total=cart.subtotal
                )
                if result.get('available'):
                    delivery_info.calculated_fee = result['fee']
                    delivery_info.save()
            except Exception:
                # Fee calculation failure should not block saving delivery info
                pass

        return Response({
            'message': 'Delivery information saved successfully.',
            'delivery_info': DeliveryInfoSerializer(delivery_info).data
        })


# ============================================================================
# GUEST CART MERGE
# ============================================================================

class MergeGuestCartView(APIView):
    """
    POST /api/cart/merge/ - Merge guest cart with user cart on login
    Requires authentication.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Merge Guest Cart",
        operation_description="Merge a guest session cart into the authenticated user's cart after login.",
        request_body=GuestCartMergeSerializer,
        responses={
            200: openapi.Response(description="Carts merged successfully."),
            404: openapi.Response(description="No guest cart found to merge."),
        }
    )
    def post(self, request):
        serializer = GuestCartMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_key = serializer.validated_data['session_key']

        try:
            guest_cart = Cart.objects.get(
                session_key=session_key,
                is_active=True,
                user__isnull=True
            )
        except Cart.DoesNotExist:
            return Response(
                {'message': 'No guest cart found to merge.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user_cart, _ = Cart.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'session_key': None}
        )

        from cart.utils import merge_carts
        merged_cart = merge_carts(user_cart, guest_cart, request.user)

        return Response({
            'message': 'Carts merged successfully.',
            'cart': CartSerializer(merged_cart).data
        })