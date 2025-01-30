from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Transaction

@shared_task
def send_payment_confirmation_email(reference):
    """
    Send a confirmation email after a successful payment.
    
    Args:
        reference (str): The Paystack payment reference.
    """
    try:
        transaction = Transaction.objects.get(reference=reference)

        subject = "Payment Confirmation"
        message = f"""
        Dear {transaction.email},

        Your payment of NGN {transaction.amount} was successful.  
        Reference: {transaction.reference}

        Thank you for your purchase!

        Best regards,  
        Bakery Shop
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.email])
    except Transaction.DoesNotExist:
        pass


@shared_task
def send_failed_payment_email(reference):
    """
    Send an email notification for a failed payment attempt.

    Args:
        reference (str): The Paystack payment reference used to identify the transaction.
    """

    try:
        transaction = Transaction.objects.get(reference=reference)

        subject = "Payment Failed"
        message = f"""
        Dear {transaction.email},

        Unfortunately, your payment of NGN {transaction.amount} failed.  
        Reference: {transaction.reference}

        Please try again or contact support.

        Regards,  
        Your Company
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [transaction.email])
    except Transaction.DoesNotExist:
        pass