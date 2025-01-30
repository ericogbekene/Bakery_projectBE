from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from cart.cart import Cart
from .serializers import OrderCreateSerializer, OrderSerializer
from .tasks import order_created
from .models import Order, OrderItem
from products.models import Product  

class OrderView(APIView):
    """
    A view for handling order creation and related operations.
    """

    @transaction.atomic
    def post(self, request):
        """
        Handle POST request to create an order.
        Creates Order and OrderItem instances, clears the cart, and triggers a Celery task.
        """
        cart = Cart(request)

        if not cart:
            return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Allow guest checkout if user is not authenticated
            user = request.user if request.user.is_authenticated else None
            order = serializer.save(user=user)

            order_items = []
            for item in cart:
                try:
                    product = Product.objects.get(id=item['product_id'])  # Ensure valid product
                    order_items.append(
                        OrderItem(
                            order=order,
                            product=product,
                            price=item['price'],
                            quantity=item['quantity']
                        )
                    )
                except Product.DoesNotExist:
                    return Response({"error": f"Product with ID {item['product_id']} not found"},
                                    status=status.HTTP_400_BAD_REQUEST)

            # Bulk insert order items
            OrderItem.objects.bulk_create(order_items)

            # Automatically update the total cost
            order.update_total_cost()

            # Clear the cart after successful order
            cart.clear()

            # Send email notification via Celery
            order_created.delay(order.id)

            # Store order ID in session for payment processing
            request.session['order_id'] = order.id

            payment_url = reverse('payment_process')
            return Response({"message": "Order created successfully", "payment_url": payment_url},
                            status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """
    Retrieves order details.
    """

    def get(self, request, order_id):
        """
        Retrieves an order by its ID.

        Args:
            order_id (int): The ID of the order to retrieve.

        Returns:
            Response: A Response object containing the serialized order data.
        """
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)