from django.shortcuts import render
from decimal import Decimal
import pypaystack
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from orders.models import Order


paystack.api_key = settings.PAYSTACK_SECRET_KEY
paystack.api_version = settings.PAYSTACK_API_VERSION


def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)
    amount = int(order.get_total_cost().quantize(Decimal('0.00')) * 100)

    callback_url = reverse('payment:payment_process')

    if request.method == 'POST':
        success_url =request.build_absolute_uri(reverse('payment:payment_complete'))
        cancel_url = request.build_absolute_uri(reverse('payment:payment_cancelled'))

        # paystack checkout session data

        session_data = {
            'mode': 'payment'
            'client_ref'
        }  