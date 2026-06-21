import uuid
from django.db import models
from orders.models import Order
from cart.models import Cart
from django.conf import settings


STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
]


class Transaction(models.Model):
    # Unique payment reference (UUID)
    reference = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique payment reference (UUID)"
    )

    # Paystack transaction ID returned after payment verification
    paystack_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Paystack transaction ID from verification response"
    )

    # Paystack access code (needed for inline payment if we switch to modal later)
    paystack_access_code = models.CharField(
        max_length=255,
        blank=True,
        help_text="Paystack access code from payment initialization"
    )

    # Cart changed from CASCADE to SET_NULL — payment records must never be deleted
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Cart this payment was initiated from"
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Order linked to this transaction"
    )

    # Email captured at transaction time — important for guest checkouts
    email = models.EmailField(
        help_text="Customer email at time of payment"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount paid in the transaction"
    )

    currency = models.CharField(
        max_length=10,
        default='NGN',
        help_text="Currency used for the transaction"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current transaction status"
    )

    # Store complete Paystack API response for debugging
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete Paystack API response"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='transactions',
        help_text="Authenticated user (null for guest checkout)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['paystack_transaction_id']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'Transaction - {self.reference} - {self.status}'