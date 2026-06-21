# payment/webhook_views.py

import json
import hmac
import hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from orders.models import Order, OrderHistory
from .models import Transaction


@csrf_exempt
def paystack_webhook(request):
    """
    POST /api/payment/webhook/
    Handle Paystack webhook events.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # ✅ Verify the webhook signature
    paystack_secret = settings.PAYSTACK_SECRET_KEY
    signature = request.headers.get('x-paystack-signature')
    
    if not signature:
        print("❌ No webhook signature found")
        return JsonResponse({'error': 'No signature'}, status=400)
    
    # ✅ Verify signature
    try:
        payload = request.body
        expected_signature = hmac.new(
            paystack_secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            print("❌ Invalid webhook signature")
            return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        print(f"❌ Signature verification error: {e}")
        return JsonResponse({'error': 'Signature verification failed'}, status=400)
    
    # ✅ Parse the webhook data
    try:
        data = json.loads(payload)
        print(f"📡 Webhook received: {data}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON payload: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # ✅ Process the event
    event = data.get('event')
    event_data = data.get('data', {})
    
    print(f"📡 Event: {event}")
    print(f"📡 Event data: {event_data}")
    
    if event == 'charge.success':
        # ✅ Payment was successful
        reference = event_data.get('reference')
        transaction_id = event_data.get('id')
        
        print(f"✅ Charge successful: {reference}")
        
        try:
            # ✅ Find the transaction
            transaction = Transaction.objects.get(reference=reference)
            
            # ✅ Update transaction
            transaction.status = 'completed'
            transaction.paystack_transaction_id = str(transaction_id)
            transaction.gateway_response = event_data
            transaction.save()
            
            # ✅ Update order
            order = transaction.order
            if order:
                order.payment_status = 'paid'
                order.paystack_transaction_id = str(transaction_id)
                order.paystack_reference = reference
                order.paystack_response = event_data
                order.payment_date = timezone.now()
                order.status = 'confirmed'
                order.save()
                
                OrderHistory.objects.create(
                    order=order,
                    action='payment_received',
                    description=f"Payment received via Paystack webhook. Reference: {reference}",
                    changed_by=transaction.user,
                    old_value='pending',
                    new_value='paid'
                )
                
                # Deactivate cart
                if order.cart:
                    order.cart.is_active = False
                    order.cart.save()
                
                print(f"✅ Order updated: {order.order_number}")
            
            return JsonResponse({'status': 'success'}, status=200)
            
        except Transaction.DoesNotExist:
            print(f"❌ Transaction not found: {reference}")
            return JsonResponse({'error': 'Transaction not found'}, status=404)
        except Exception as e:
            print(f"❌ Error processing webhook: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    elif event == 'charge.failed':
        # ✅ Payment failed
        reference = event_data.get('reference')
        print(f"❌ Charge failed: {reference}")
        
        try:
            transaction = Transaction.objects.get(reference=reference)
            transaction.status = 'failed'
            transaction.gateway_response = event_data
            transaction.save()
            
            if transaction.order:
                transaction.order.payment_status = 'failed'
                transaction.order.save()
            
            return JsonResponse({'status': 'success'}, status=200)
        except Transaction.DoesNotExist:
            print(f"❌ Transaction not found: {reference}")
            return JsonResponse({'error': 'Transaction not found'}, status=404)
    
    elif event == 'refund.processed':
        # ✅ Refund processed
        reference = event_data.get('reference')
        print(f"🔄 Refund processed: {reference}")
        
        try:
            transaction = Transaction.objects.get(reference=reference)
            transaction.status = 'refunded'
            transaction.gateway_response = event_data
            transaction.save()
            
            if transaction.order:
                transaction.order.payment_status = 'refunded'
                transaction.order.save()
            
            return JsonResponse({'status': 'success'}, status=200)
        except Transaction.DoesNotExist:
            print(f"❌ Transaction not found: {reference}")
            return JsonResponse({'error': 'Transaction not found'}, status=404)
    
    else:
        print(f"⚠️ Unhandled event: {event}")
        return JsonResponse({'status': 'ignored'}, status=200)