from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .cart import Cart
from products.models import Product
from .serializers import CartItemSerializer, CartDetailSerializer, CartRemoveSerializer


class CartAddUpdateView(APIView):
    """
    View to add or update items in the cart.
    """
    def post(self, request, *args, **kwargs):
        """
        Add or update items in the cart.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: A Response object containing the result of the operation.
        """
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        override_quantity = serializer.validated_data['override_quantity']

        # Get the product object
        product = get_object_or_404(Product, id=product_id)

        # Initialize the cart and add/update item
        cart = Cart(request)
        cart.add(product=product, quantity=quantity, override_quantity=override_quantity)

        return Response({'message': 'Product added/updated successfully.'}, status=status.HTTP_200_OK)


class CartRemoveView(APIView):
    """
    View to remove items from the cart.
    """
    def delete(self, request, *args, **kwargs):
        """
        View to remove items from the cart.
        
        Deletes a product from the cart.
        
        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            Response: A Response object containing the result of the operation.
        """
        serializer = CartRemoveSerializer(data=request.data)
        if serializer.is_valid():  # Check if the serializer is valid
            product_id = serializer.validated_data['product_id']
            cart = Cart(request)
            product = get_object_or_404(Product, id=product_id)
            cart.remove(product)

            return Response({'message': 'Product removed successfully.'}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid product_id'}, status=status.HTTP_400_BAD_REQUEST)


class CartDetailView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Retrieves the current cart and calculates the total price, discount, and total price after discount.

        Returns:
            Response: A Response object containing the cart items, total price, discount, and total price after discount.
        """
        cart = Cart(request)
        cart_items = list(cart)
        total_price = cart.get_total_price()
        discount = cart.get_discount()
        total_after_discount = cart.get_total_price_after_discount()

        return Response({
            "items": cart_items,
            "total_price": total_price,
            "discount": discount,
            "total_after_discount": total_after_discount,
        }, status=status.HTTP_200_OK)


class CartClearView(APIView):
    """
    View to clear the cart.
    """
    def post(self, request, *args, **kwargs):
        """
        Clear the cart.

        Returns:
            Response: A Response object containing the result of the operation.
        """
        cart = Cart(request)
        cart.clear()
        return Response({"message": "Cart cleared successfully."}, status=status.HTTP_200_OK)
