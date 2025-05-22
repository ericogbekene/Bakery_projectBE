from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Model representing a product category."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return self.available
        return self.stock_quantity > 0 and self.available
    
    def is_low_stock(self):
        """Check if product stock is below threshold."""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    def reduce_stock(self, quantity):
        """Reduce stock by given quantity."""
        if self.track_inventory:
            if self.stock_quantity >= quantity:
                self.stock_quantity -= quantity
                self.save()
                return True
            return False
        return True  # Always succeed if not tracking inventory
    
    def increase_stock(self, quantity):
        """Increase stock by given quantity."""
        if self.track_inventory:
            self.stock_quantity += quantity
            self.save()
    
    def get_absolute_url(self):
        """Return the URL for this category."""
        return reverse('category_detail', args=[self.slug])
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Model representing a product in the store."""
    category = models.ForeignKey(
        Category, 
        related_name='products', 
        on_delete=models.CASCADE, 
        null=True,
        blank=True
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)  # Removed unique=True for category-specific uniqueness
    image = models.ImageField(
        upload_to='products/%Y/%m/%d', 
        blank=True, 
        null=True
    )
    description = models.TextField(blank=True, null=True)
    
    # Price with validation
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    # Stock management
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current stock level"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text="Alert when stock falls below this level"
    )
    track_inventory = models.BooleanField(
        default=True,
        help_text="Whether to track inventory for this product"
    )
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return self.available
        return self.stock_quantity > 0 and self.available
    
    def is_low_stock(self):
        """Check if product stock is below threshold."""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    def get_absolute_url(self):
        """Return the URL for this product."""
        return reverse('product_detail', args=[self.id, self.slug])
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['available']),
            models.Index(fields=['stock_quantity']),
            models.Index(fields=['category', 'available']),
        ]
        # Unique together constraint for category-specific slug uniqueness
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_product_slug_per_category'
            ),
        ]
    
    def __str__(self):
        """Return a string representation of the product."""
        return self.name