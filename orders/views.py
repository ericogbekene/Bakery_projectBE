from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cart.cart import Cart
from .serializers import OrderCreateSerializer
from .tasks import order_created
from .models import Order, OrderItem



class OrderView(APIView):
    """
    A view for handling order creation and related operations.
    """

    def post(self, request):
        """
        Handle POST request to create an order. This will create an instance of 
        Order and OrderItem models. It will also clear the cart and trigger celery 
        task to send an email notification.
        """
        cart = Cart(request)
        serializer = OrderCreateSerializer(data=request.POST)
        if serializer.is_valid():
            order = serializer.save()
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                ) for item in cart
            ])
            cart.clear()
            order_created.delay(order.id)
            request.session['order_id'] = order.id
            # Redirect to payment process
            return redirect(reverse('payment_process'))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




from django.views.generic import View

class PaymentProcessView(View):
    def get(self, request):
        # Create a Paystack checkout session
        checkout_session = Checkout.create(
            {
                "amount": 10000,
                "currency": "NGN",
                "customer": {
                    "email": "customer@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "metadata": {
                    "order_id": "12345",
                    "customer_id": "67890",
                },
                "callback_url": reverse("payment_completed"),
                "cancel_url": reverse("payment_canceled"),
            }
        )

        # Redirect the client to the Paystack-hosted payment form
        return redirect(checkout_session.url)