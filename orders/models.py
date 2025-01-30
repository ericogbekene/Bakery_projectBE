from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Max
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from django.db import IntegrityError


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(db_index=True)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['email', 'paid']),
            models.Index(fields=['status']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f'Order {self.order_number} - {self.status}'

    def get_total_cost(self):
        """Calculate total cost from OrderItems"""
        return self.items.aggregate(
            total_cost=Sum(
                ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
            )
        )['total_cost'] or 0

    def update_total_cost(self):
        """Update the total cost of the order"""
        self.total_cost = self.get_total_cost()
        self.save(update_fields=['total_cost'])

    def save(self, *args, **kwargs):
        """Generate a unique order number before saving"""
        if not self.order_number:
            today = now().strftime('%Y%m%d')

            # Get last order for today
            last_order = Order.objects.filter(order_number__startswith=today).aggregate(
                Max('order_number')
            )['order_number__max']

            if last_order:
                last_number = int(last_order.split('-')[-1])
                new_number = f"{last_number + 1:05d}"
            else:
                new_number = "00001"

            self.order_number = f"{today}-{new_number}"

            # Handle uniqueness to avoid IntegrityError
            attempt = 0
            while attempt < 5:
                try:
                    super().save(*args, **kwargs)
                    break  # Exit if save succeeds
                except IntegrityError:
                    last_number += 1  # Increment and retry
                    self.order_number = f"{today}-{last_number:05d}"
                    attempt += 1
        else:
            super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def __str__(self):
        return f"OrderItem {self.id} - Order {self.order.order_number}"

    def get_cost(self):
        return self.price * self.quantity
