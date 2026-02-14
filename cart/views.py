# from django.shortcuts import get_object_or_404
# from django.http import JsonResponse
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import AllowAny
# from decimal import Decimal
# import json

# from products.models import Product
# from .models import (
#     Cart, CartItem, CakeCustomizationOption, 
#     CakeSizePrice, CakeFlavorPrice
# )
# from .serializers import (
#     CartItemDetailSerializer, CartSummarySerializer,
#     CartItemCreateUpdateSerializer, PricingInfoSerializer,
#     CakeCustomizationOptionSerializer, CakeSizePriceSerializer,
#     CakeFlavorPriceSerializer
# )

# # Import utility functions
# try:
#     from .utils import get_or_create_cart, get_cart_item_count
# except ImportError:
#     # Fallback if utils.py not available
#     pass


# # ============================================================================
# # PRICING & PRODUCT INFO API ENDPOINTS
# # ============================================================================

# class ProductDetailAPIView(APIView):
#     """
#     Get product details with all pricing information.
#     Provides customization options, size prices, and flavor multipliers.
    
#     GET /api/products/{product_id}/details/
    
#     Response:
#     {
#         "success": true,
#         "product": {
#             "id": 1,
#             "name": "Chocolate Cake",
#             "description": "...",
#             "image": "https://...",
#             "base_price": "10000.00"
#         },
#         "pricing_info": {
#             "customization_options": [...],
#             "size_prices": [...],
#             "flavor_prices": [...]
#         }
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request, product_id):
#         try:
#             product = Product.objects.get(id=product_id)
#         except Product.DoesNotExist:
#             return Response(
#                 {'success': False, 'error': 'Product not found'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         # Get all active pricing data
#         customizations = CakeCustomizationOption.objects.filter(is_active=True)
#         sizes = CakeSizePrice.objects.all()
#         flavors = CakeFlavorPrice.objects.all()
        
#         pricing_data = {
#             'customizations': customizations,
#             'sizes': sizes,
#             'flavors': flavors,
#         }
        
#         pricing_serializer = PricingInfoSerializer(pricing_data)
        
#         return Response({
#             'success': True,
#             'product': {
#                 'id': product.id,
#                 'name': product.name,
#                 'description': product.description,
#                 'image': product.image.url if product.image else None,
#                 'base_price': str(product.price) if hasattr(product, 'price') else None,
#             },
#             'pricing_info': pricing_serializer.data,
#         }, status=status.HTTP_200_OK)


# class PricingInfoAPIView(APIView):
#     """
#     Get all pricing information.
#     Useful for initializing the pricing calculator on frontend.
    
#     GET /api/pricing/
    
#     Response:
#     {
#         "success": true,
#         "customizations": [...],
#         "sizes": [...],
#         "flavors": [...]
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request):
#         customizations = CakeCustomizationOption.objects.filter(is_active=True)
#         sizes = CakeSizePrice.objects.all()
#         flavors = CakeFlavorPrice.objects.all()
        
#         return Response({
#             'success': True,
#             'customizations': CakeCustomizationOptionSerializer(customizations, many=True).data,
#             'sizes': CakeSizePriceSerializer(sizes, many=True).data,
#             'flavors': CakeFlavorPriceSerializer(flavors, many=True).data,
#         }, status=status.HTTP_200_OK)


# class CalculateCakePriceAPIView(APIView):
#     """
#     Calculate price for a custom cake based on selections.
#     Use this for real-time pricing updates on frontend.
    
#     POST /api/calculate-cake-price/
    
#     Request Body:
#     {
#         "size": "10",
#         "flavor_1": "Vanilla",
#         "flavor_2": "Chocolate",
#         "cake_topper": 2,
#         "candle": 4,
#         "birthday_card": 1,
#         "chocolate": 0,
#         "wine": 1,
#         "whiskey_200ml": 0,
#         "quantity": 1
#     }
    
#     Response:
#     {
#         "success": true,
#         "pricing": {
#             "base_price": "32500.00",
#             "customization_cost": "15000.00",
#             "price_per_cake": "47500.00",
#             "quantity": 1,
#             "total_price": "47500.00",
#             "customization_breakdown": [...]
#         }
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         try:
#             data = request.data
            
#             # Get size price
#             size = data.get('size', '8')
#             base_price = Decimal('0.00')
            
#             try:
#                 size_obj = CakeSizePrice.objects.get(size=size)
#                 base_price = size_obj.base_price
#             except CakeSizePrice.DoesNotExist:
#                 return Response(
#                     {'success': False, 'error': f'Size {size} not found'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Apply flavor multiplier
#             flavor = data.get('flavor_1', '')
#             flavor_multiplier = Decimal('1.0')
            
#             if flavor:
#                 try:
#                     flavor_obj = CakeFlavorPrice.objects.get(flavor=flavor)
#                     flavor_multiplier = flavor_obj.price_multiplier
#                 except CakeFlavorPrice.DoesNotExist:
#                     pass
            
#             adjusted_base_price = base_price * flavor_multiplier
            
#             # Calculate customization costs
#             customization_cost = Decimal('0.00')
#             customization_breakdown = []
            
#             customizations = {
#                 'cake_topper': ('topper', 'Cake Topper'),
#                 'candle': ('candle', 'Candle'),
#                 'birthday_card': ('birthday_card', 'Birthday Card'),
#                 'chocolate': ('chocolate', 'Chocolate Box'),
#                 'wine': ('wine', 'Wine Bottle'),
#                 'whiskey_200ml': ('whiskey', 'Whiskey (200ml)'),
#             }
            
#             for field_name, (option_type, display_name) in customizations.items():
#                 quantity = int(data.get(field_name, 0))
                
#                 if quantity > 0:
#                     try:
#                         option = CakeCustomizationOption.objects.get(
#                             customization_type=option_type
#                         )
#                         cost = option.price_per_unit * quantity
#                         customization_cost += cost
                        
#                         customization_breakdown.append({
#                             'name': display_name,
#                             'quantity': quantity,
#                             'unit_price': str(option.price_per_unit),
#                             'total_cost': str(cost)
#                         })
#                     except CakeCustomizationOption.DoesNotExist:
#                         pass
            
#             # Calculate total
#             price_per_cake = adjusted_base_price + customization_cost
#             quantity = int(data.get('quantity', 1))
#             total_price = price_per_cake * quantity
            
#             return Response({
#                 'success': True,
#                 'pricing': {
#                     'base_price': str(adjusted_base_price),
#                     'customization_cost': str(customization_cost),
#                     'price_per_cake': str(price_per_cake),
#                     'quantity': quantity,
#                     'total_price': str(total_price),
#                     'customization_breakdown': customization_breakdown
#                 }
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# # ============================================================================
# # CART MANAGEMENT API ENDPOINTS
# # ============================================================================

# class AddToCartAPIView(APIView):
#     """
#     Add a customized cake to cart.
    
#     POST /api/cart/add/
    
#     Request Body:
#     {
#         "product": 1,
#         "quantity": 1,
#         "size": "12",
#         "flavour_1": "Marble",
#         "flavour_2": "Vanilla",
#         "colours": "pink, white",
#         "cake_topper": 1,
#         "candle": 4,
#         "birthday_card": 1,
#         "chocolate": 0,
#         "wine": 1,
#         "whiskey_200ml": 0,
#         "additional_notes": "Make it extra moist"
#     }
    
#     Response:
#     {
#         "success": true,
#         "message": "Item added to cart successfully",
#         "cart_item": {...},
#         "cart_total": "47500.00",
#         "item_count": 1
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         try:
#             # Get or create cart
#             cart = get_or_create_cart(request)
            
#             # Validate and create cart item
#             serializer = CartItemCreateUpdateSerializer(data=request.data)
#             if serializer.is_valid():
#                 cart_item = serializer.save(cart=cart)
                
#                 # Return detailed cart item info
#                 response_serializer = CartItemDetailSerializer(cart_item)
#                 return Response({
#                     'success': True,
#                     'message': 'Item added to cart successfully',
#                     'cart_item': response_serializer.data,
#                     'cart_total': str(cart.total_price),
#                     'item_count': cart.item_count,
#                 }, status=status.HTTP_201_CREATED)
            
#             return Response({
#                 'success': False,
#                 'errors': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# class UpdateCartItemAPIView(APIView):
#     """
#     Update a cart item (change quantity or customizations).
    
#     PUT /api/cart/item/{cart_item_id}/
    
#     Request Body: Same as add to cart (with changes)
    
#     Response:
#     {
#         "success": true,
#         "message": "Cart item updated successfully",
#         "cart_item": {...},
#         "cart_total": "47500.00"
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def put(self, request, cart_item_id):
#         try:
#             cart_item = CartItem.objects.get(id=cart_item_id)
            
#             # Verify cart ownership
#             cart = get_or_create_cart(request)
#             if cart_item.cart_id != cart.id:
#                 return Response(
#                     {'success': False, 'error': 'This item does not belong to your cart'},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
            
#             # Update the item
#             serializer = CartItemCreateUpdateSerializer(cart_item, data=request.data, partial=True)
#             if serializer.is_valid():
#                 updated_item = serializer.save()
                
#                 response_serializer = CartItemDetailSerializer(updated_item)
#                 return Response({
#                     'success': True,
#                     'message': 'Cart item updated successfully',
#                     'cart_item': response_serializer.data,
#                     'cart_total': str(cart.total_price),
#                 }, status=status.HTTP_200_OK)
            
#             return Response({
#                 'success': False,
#                 'errors': serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         except CartItem.DoesNotExist:
#             return Response(
#                 {'success': False, 'error': 'Cart item not found'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# class RemoveFromCartAPIView(APIView):
#     """
#     Remove an item from cart.
    
#     DELETE /api/cart/item/{cart_item_id}/
    
#     Response:
#     {
#         "success": true,
#         "message": "Item removed from cart",
#         "cart_total": "0.00",
#         "item_count": 0
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def delete(self, request, cart_item_id):
#         try:
#             cart_item = CartItem.objects.get(id=cart_item_id)
            
#             # Verify cart ownership
#             cart = get_or_create_cart(request)
#             if cart_item.cart_id != cart.id:
#                 return Response(
#                     {'success': False, 'error': 'This item does not belong to your cart'},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
            
#             # Delete the item
#             cart_item.delete()
            
#             return Response({
#                 'success': True,
#                 'message': 'Item removed from cart',
#                 'cart_total': str(cart.total_price),
#                 'item_count': cart.item_count,
#             }, status=status.HTTP_200_OK)
        
#         except CartItem.DoesNotExist:
#             return Response(
#                 {'success': False, 'error': 'Cart item not found'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# class CartDetailAPIView(APIView):
#     """
#     Get full cart details with all items.
    
#     GET /api/cart/
    
#     Response:
#     {
#         "success": true,
#         "cart": {
#             "id": 1,
#             "items": [...],
#             "total_price": "47500.00",
#             "item_count": 1,
#             "is_active": true,
#             "created_at": "2024-01-29T10:30:00Z",
#             "updated_at": "2024-01-29T10:30:00Z"
#         }
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request):
#         try:
#             cart = get_or_create_cart(request)
#             serializer = CartSummarySerializer(cart)
            
#             return Response({
#                 'success': True,
#                 'cart': serializer.data
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# class ClearCartAPIView(APIView):
#     """
#     Clear all items from cart.
    
#     POST /api/cart/clear/
    
#     Response:
#     {
#         "success": true,
#         "message": "Cart cleared successfully",
#         "cart_total": "0.00",
#         "item_count": 0
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         try:
#             cart = get_or_create_cart(request)
#             cart.items.all().delete()
            
#             return Response({
#                 'success': True,
#                 'message': 'Cart cleared successfully',
#                 'cart_total': str(cart.total_price),
#                 'item_count': cart.item_count,
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# class CartItemCountAPIView(APIView):
#     """
#     Get cart item count.
#     Useful for header badge showing number of items in cart.
    
#     GET /api/cart/count/
    
#     Response:
#     {
#         "success": true,
#         "count": 3
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request):
#         count = get_cart_item_count(request)
#         return Response({
#             'success': True,
#             'count': count
#         }, status=status.HTTP_200_OK)


# class CartTotalAPIView(APIView):
#     """
#     Get cart total price.
    
#     GET /api/cart/total/
    
#     Response:
#     {
#         "success": true,
#         "total": "47500.00"
#     }
#     """
#     permission_classes = [AllowAny]
    
#     def get(self, request):
#         try:
#             cart = get_or_create_cart(request)
#             return Response({
#                 'success': True,
#                 'total': str(cart.total_price)
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             return Response(
#                 {'success': False, 'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )