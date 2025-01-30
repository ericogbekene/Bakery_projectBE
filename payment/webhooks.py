import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction
from orders.models import Order
from .tasks import send_payment_confirmation_email, send_failed_payment_email

@csrf_exempt
def paystack_webhook(request):
    """
    Handles Paystack payment webhook, including success and failure events.
    """
    try:
        payload = json.loads(request.body)
        event = payload.get('event')
        data = payload.get('data', {})

        reference = data.get("reference")

        if event == "charge.success" and data.get("status") == "success":
            try:
                transaction = Transaction.objects.get(reference=reference)
            except Transaction.DoesNotExist:
                return JsonResponse({"error": "Transaction not found"}, status=404)

            # Update transaction and order status
            transaction.status = "success"
            transaction.save()

            order = transaction.order
            order.paid = True
            order.save()
            
            # Send payment confirmation email
            send_payment_confirmation_email.delay(reference)

            return JsonResponse({"message": "Payment confirmed"}, status=200)

        elif event == "charge.failed":
            try:
                transaction = Transaction.objects.get(reference=reference)
            except Transaction.DoesNotExist:
                return JsonResponse({"error": "Transaction not found"}, status=404)

            # Mark transaction as failed
            transaction.status = "failed"
            transaction.save()

            # Send failed payment alert
            send_failed_payment_email.delay(reference)

            return JsonResponse({"message": "Payment failed, alert sent"}, status=200)

        return JsonResponse({"message": "Unhandled event"}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
