from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .cart import Cart
from products.models import Product
from .serializers import CartItemSerializer


class CartAddUpdateView(APIView):
    """
    View to add or update items in the cart.
    """
    def post(self, request, *args, **kwargs):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        override_quantity = serializer.validated_data['override_quantity']

        # Get the product object
        product = get_object_or_404(Product, id=product_id)
        # Initialize the cart
        cart = Cart(request)
        # Add or update the product in the cart
        cart.add(product=product, quantity=quantity, override_quantity=override_quantity)

        return Response({'message': 'Product added/updated successfully.'}, status=status.HTTP_200_OK)


class CartRemoveView(APIView):
    """
    View to remove items from the cart.
    """
    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)

        return Response({'message': 'Product removed successfully.'}, status=status.HTTP_200_OK)


class CartDetailView(APIView):
    """
    View to display cart items and totals.
    """
    def get(self, request, *args, **kwargs):
        cart = Cart(request)
        cart_items = list(cart)
        total_price = cart.get_total_price()

        return Response({
            'items': cart_items,
            'total_price': total_price
        }, status=status.HTTP_200_OK)
