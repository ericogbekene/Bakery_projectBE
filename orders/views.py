from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from cart.cart import Cart
from .serializers import OrderCreateSerializer, OrderSerializer, OrderItemSerializer
from .tasks import order_created
from .models import Order, OrderItem
from products .models import Product

class OrderView(APIView):
    """
    A view for handling order creation and related operations.
    """

    @transaction.atomic
    def post(self, request):
        """
        Handle POST request to create an order. This will create instances of
        Order and OrderItem models, clear the cart, and trigger a Celery task
        to send an email notification.
        """
        cart = Cart(request)

        if not cart:
            return Response({"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()

            # Retrieve Product instances from the database in bulk
            product_ids = [item['product']['id'] for item in cart]
            products = Product.objects.in_bulk(product_ids)

            order_items = [
                OrderItem(
                    order=order,
                    product=products[item['product']['id']],
                    price=item['price'],
                    quantity=item['quantity']
                ) for item in cart
            ]
            OrderItem.objects.bulk_create(order_items)

            # Calculate and update the total cost
            total_cost = sum(item.get_cost() for item in order_items)
            order.total_cost = total_cost
            order.save()

            cart.clear()
            order_created.delay(order.id)
            request.session['order_id'] = order.id

            return Response({"message": "Order created successfully"}, status=status.HTTP_201_CREATED)

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