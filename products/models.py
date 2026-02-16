from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
from cloudinary import CloudinaryImage


class Category(models.Model):
    """
    Represents a category for products (e.g., Birthday, Wedding, Anniversary).
    Used for organizing products in the store.
    """
    name = models.CharField(
        max_length=200, 
        help_text="The name of the category (e.g., Birthday, Wedding)."
    )
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        help_text="A URL-friendly identifier for the category."
    )

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
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents a product in the bakery store.
    Can be either a Cake (customizable) or Pastry (fixed product).
    """
    
    # Product type choices
    PRODUCT_TYPES = [
        ('cake', 'Cake'),
        ('pastry', 'Pastry'),
    ]
    
    # Cake covering choices
    COVERING_CHOICES = [
        ('buttercream', 'Buttercream'),
        ('fondant', 'Fondant'),
        ('cream_cheese', 'Cream Cheese Frosting'),
        ('whipped_cream', 'Whipped Cream'),
        ('naked', 'Naked Cake'),
        ('ganache', 'Chocolate Ganache'),
    ]
    
    # Basic product information
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional category for organizing products (e.g., Birthday, Wedding)."
    )
    
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        default='cake',
        help_text="Cake: customizable, made-to-order. Pastry: fixed product."
    )
    
    name = models.CharField(
        max_length=200, 
        help_text="The name of the product (e.g., 'Butterfly Cake', 'Chocolate Croissant')."
    )
    
    slug = models.SlugField(
        max_length=200, 
        help_text="A URL-friendly identifier for the product."
    )
    
    # Image field using Cloudinary
    image = CloudinaryField(
        'image',
        folder='products_images',
        transformation=[{'quality': 'auto', 'fetch_format': 'auto'}],
        blank=True,
        null=True,
        help_text="An image of the product. Recommended size: 800x600px."
    )
    
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text="A detailed description of the product."
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="For cakes: Design base fee. For pastries: Fixed selling price."
    )
    
    # Cake-specific fields (only relevant when product_type='cake')
    layers = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        help_text="Number of cake layers (e.g., 2, 4). Required for cakes."
    )
    
    covering = models.CharField(
        max_length=50,
        choices=COVERING_CHOICES,
        null=True,
        blank=True,
        help_text="Type of cake covering. Required for cakes."
    )
    
    inspiration = models.TextField(
        blank=True,
        null=True,
        help_text="Design inspiration or story behind the cake (optional)."
    )
    
    preparation_days = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        null=True,
        blank=True,
        help_text="Minimum days needed to prepare this product. Required for cakes."
    )
    
    # Product availability
    available = models.BooleanField(
        default=True,
        help_text="Whether the product is available for purchase. Uncheck to hide from store."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to automatically generate a slug if one is not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        """
        Custom validation based on product_type.
        """
        from django.core.exceptions import ValidationError
        
        if self.product_type == 'cake':
            # Validate required fields for cakes
            if not self.layers:
                raise ValidationError({'layers': 'Layers is required for cakes.'})
            if not self.covering:
                raise ValidationError({'covering': 'Covering type is required for cakes.'})
            if not self.preparation_days:
                raise ValidationError({'preparation_days': 'Preparation days is required for cakes.'})
            
            # Additional cake-specific validation
            if self.layers < 1:
                raise ValidationError({'layers': 'Cake must have at least 1 layer.'})
            if self.preparation_days < 1:
                raise ValidationError({'preparation_days': 'Preparation days must be at least 1.'})
            
        elif self.product_type == 'pastry':
            if self.layers not in [None, '']:
                raise ValidationError({'layers': 'Layers field should be empty for pastries.'})
            if self.covering not in [None, '']:
                raise ValidationError({'covering': 'Covering field should be empty for pastries.'})
            if self.inspiration not in [None, '']:
                raise ValidationError({'inspiration': 'Inspiration field should be empty for pastries.'})
            if self.preparation_days not in [None, '']:
                raise ValidationError({'preparation_days': 'Preparation days should be empty for pastries.'})
            
        super().clean()

    @property
    def is_cake(self):
        """Helper property to check if product is a cake."""
        return self.product_type == 'cake'

    @property
    def is_pastry(self):
        """Helper property to check if product is a pastry."""
        return self.product_type == 'pastry'

    def get_absolute_url(self):
        """
        Returns the absolute URL for a product instance.
        """
        return reverse('product_detail', args=[self.id, self.slug])
    
    # Cloudinary image URL properties
    @property
    def image_url(self):
        """Get the full Cloudinary URL for the image."""
        if self.image:
            return self.image.url
        return None
    
    @property
    def thumbnail_url(self):
        """Get a thumbnail version from Cloudinary (150x150)."""
        if self.image:
            public_id = self.image.public_id
            # Fixed the typo: changed 'cake' to 'crop'
            thumbnail = CloudinaryImage(public_id).build_url(
                transformation=[
                    {'width': 150, 'height': 150, 'crop': 'fill', 'gravity': 'center'},
                    {'quality': 'auto', 'fetch_format': 'auto'}    
                ]
            )
            return thumbnail
        return None
    
    @property
    def medium_image_url(self):
        """Get a medium-size version from Cloudinary (400x300)."""
        if self.image:
            public_id = self.image.public_id
            # Fixed the typo: changed 'cake' to 'fit'
            medium = CloudinaryImage(public_id).build_url(
                transformation=[
                    {'width': 400, 'height': 300, 'crop': 'fit'},
                    {'quality': 'auto', 'fetch_format': 'auto'}
                ]
            )
            return medium
        return None
    
    @property
    def large_image_url(self):
        """Get a large version from Cloudinary (800x600)."""
        if self.image:
            public_id = self.image.public_id
            # Fixed the typo: changed 'cake' to 'fit'
            large = CloudinaryImage(public_id).build_url(
                transformation=[
                    {'width': 800, 'height': 600, 'crop': 'fit'},
                    {'quality': 'auto', 'fetch_format': 'auto'}
                ]
            )
            return large
        return None

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['available']),
            models.Index(fields=['product_type', 'available']),
            models.Index(fields=['category', 'available']),
        ]
        # Ensures that each product's slug is unique within its category
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_product_slug_per_category'
            ),
        ]

    def __str__(self):
        product_type_display = dict(self.PRODUCT_TYPES).get(self.product_type, self.product_type)
        return f"{self.name} ({product_type_display})"