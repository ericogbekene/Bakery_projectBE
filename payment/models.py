import uuid
from django.db import models
from orders.models import Order

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('success', 'Success'),
    ('failed', 'Failed'),
]

class Transaction(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Return a string representation of the payment which includes the payment
        reference and status.
        """
        
        return f'Payment {self.reference} - {self.status}'

    def save(self, *args, **kwargs):
        """
        Generate a unique reference for the transaction if it doesn't already exist.
        """
        if not self.reference:
            self.reference = str(uuid.uuid4().hex[:12])  # Unique 12-character reference
        super().save(*args, **kwargs)
