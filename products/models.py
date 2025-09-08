from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator


class Category(models.Model):
    """
    Represents a category for products.

    Each category has a unique name and a slug for URL-friendly identifiers.
    """
    name = models.CharField(max_length=200, help_text="The name of the category.")
    slug = models.SlugField(max_length=200, unique=True, help_text="A URL-friendly identifier for the category.")

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to automatically generate a slug if one is not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns the absolute URL for a category instance.
        """
        return reverse('category_detail', args=[self.slug])

    class Meta:
        """
        Meta options for the Category model.
        """
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        """
        Returns the string representation of the category, which is its name.
        """
        return self.name


class Product(models.Model):
    """
    Represents a product in the store.

    Each product belongs to a category and has various attributes like name,
    description, price, and stock information.
    """
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The category this product belongs to."
    )
    name = models.CharField(max_length=200, help_text="The name of the product.")
    slug = models.SlugField(max_length=200, help_text="A URL-friendly identifier for the product.")
    image = models.ImageField(
        upload_to='products/%Y/%m/%d',
        blank=True,
        null=True,
        help_text="An image of the product."
    )
    description = models.TextField(blank=True, null=True, help_text="A detailed description of the product.")

    # Price with validation
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="The price of the product."
    )

    # Stock management
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="The current quantity of the product in stock."
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text="The stock level at which to trigger a low stock alert."
    )
    track_inventory = models.BooleanField(
        default=True,
        help_text="Whether to track inventory for this product."
    )
    available = models.BooleanField(default=True, help_text="Whether the product is available for purchase.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the product was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="The date and time the product was last updated.")

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to automatically generate a slug if one is not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_in_stock(self):
        """
        Checks if the product is in stock.

        If inventory is not tracked, it relies on the 'available' flag.
        Otherwise, it checks if the stock quantity is greater than zero.
        """
        if not self.track_inventory:
            return self.available
        return self.stock_quantity > 0 and self.available

    def is_low_stock(self):
        """
        Checks if the product's stock is below the low stock threshold.

        If inventory is not tracked, this will always be False.
        """
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
        """
        Returns the absolute URL for a product instance.
        """
        return reverse('product_detail', args=[self.id, self.slug])

    class Meta:
        """
        Meta options for the Product model.
        """
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['available']),
            models.Index(fields=['stock_quantity']),
            models.Index(fields=['category', 'available']),
        ]
        # Ensures that each product's slug is unique within its category.
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_product_slug_per_category'
            ),
        ]

    def __str__(self):
        """
        Returns the string representation of the product, which is its name.
        """
        return self.name