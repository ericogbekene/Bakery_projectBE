from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    defining a model for Products
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to='products/product-image', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        
        """
        Return a string representation of the product which includes the product name.
        """
        return self.name


class Order(models.Model):
    """
    Model for a Custom Order
    """
    products = models.ManyToManyField(Product, related_name='customer_orders')
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Return a string representation of the order which includes the order id and the quantity.
        """
        return f"Order {self.id} - Quantity: {self.quantity}"


class OrderItem(models.Model):
    """
    Model for an Order Item
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"

    def total_price(self):
        """
        Calculate the total price of all items in the cart.

        Returns:
            Decimal: The total price of all items in the cart.
        """
        return sum(item.total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        
        """
        Return a string representation of the cart item, indicating the quantity and product name.
        """
        return f"{self.quantity} of {self.product.name} in car"

    def total_price(self):
        """
            Calculate the total price for the cart item based on its quantity and product price.

            Returns:
                Decimal: The total price for the cart item.
        """
        return self.quantity * self.product.price