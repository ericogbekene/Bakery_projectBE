from django.db import models

# Create your models here.

class Products(models.Model):
    """
    defining a model for Products
    """
    name = models.CharField(max_length=258)