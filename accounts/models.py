# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class CustomUser(AbstractUser):
    """Custom user model for bakery customers"""
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=11,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        blank=True,
        null=True
    )
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address Information
    address_line_1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='US')
    
    # Account metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'bakery_users'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not hasattr(self, 'profile'):
            from .models import CustomerProfile
            CustomerProfile.objects.create(user=self)


    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])

class CustomerProfile(models.Model):
    """Extended profile information for customers"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    
    # Loyalty program
    loyalty_points = models.PositiveIntegerField(default=0)
    membership_tier = models.CharField(
        max_length=20,
        choices=[
            ('bronze', 'Bronze'),
            ('silver', 'Silver'),
            ('gold', 'Gold'),
            ('platinum', 'Platinum'),
        ],
        default='bronze'
    )
    
    # Purchase history summary
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    favorite_category = models.CharField(max_length=100, blank=True)
    
    # Preferences
    preferred_pickup_time = models.TimeField(null=True, blank=True)
    preferred_delivery_day = models.CharField(
        max_length=10,
        choices=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
            ('sunday', 'Sunday'),
        ],
        blank=True
    )
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    def update_loyalty_tier(self):
        """Update membership tier based on total spent"""
        if self.total_spent >= 1000:
            self.membership_tier = 'platinum'
        elif self.total_spent >= 500:
            self.membership_tier = 'gold'
        elif self.total_spent >= 200:
            self.membership_tier = 'silver'
        else:
            self.membership_tier = 'bronze'
        self.save()
    
    def add_loyalty_points(self, points):
        """Add loyalty points to customer account"""
        self.loyalty_points += points
        self.save()
    
    def redeem_loyalty_points(self, points):
        """Redeem loyalty points (if sufficient balance)"""
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save()
            return True
        return False


