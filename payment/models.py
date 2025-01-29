from django.db import models

STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

class Transaction(models.Model):
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.email} - {self.amount}'