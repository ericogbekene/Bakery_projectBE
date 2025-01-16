from rest_framework import viewsets, status
from rest_framework.response import Response
from cart.cart import Cart
from .models import Order, OrderItem
from .serializers import OrderCreateSerializer


class OrderViewSet(viewsets.ViewSet):
    """
    A ViewSet for handling order creation and related operations.
    """

    def create(self, request, *args, **kwargs):
        """
        Handle the creation of an order.
        """
        cart = Cart(request)  # Initialize the cart
        serializer = OrderCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Save the order instance
            order = serializer.save()

            # Create OrderItem entries for each item in the cart
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            # Clear the cart
            cart.clear()

            # Return a success response
            return Response(
                {
                    "message": "Order created successfully.",
                    "order_id": order.id
                },
                status=status.HTTP_201_CREATED
            )

        # Return a validation error response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    