from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from django.db import transaction
from decimal import Decimal
from django.conf import settings


# ============================================================================
# CUSTOMIZATION PRICING MODELS
# ============================================================================

class CakeCustomizationOption(models.Model):
    """
    Store all possible cake customization options with their prices.
    Examples: cake toppers, candles, chocolate boxes, wine bottles, etc.
    """
    CUSTOMIZATION_TYPES = [
        ('topper', 'Cake Topper'),
        ('candle', 'Candle'),
        ('birthday_card', 'Birthday Card'),
        ('chocolate', 'Chocolate Box'),
        ('wine', 'Wine Bottle'),
        ('whiskey', 'Whiskey Bottle (200ml)'),
    ]
    
    customization_type = models.CharField(
        max_length=50,
        choices=CUSTOMIZATION_TYPES,
        unique=True
    )
    
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Price per single unit of this customization"
    )
    
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., 'Premium gold cake topper', 'Scented vanilla candle'"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Disable to hide from customer selection"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['customization_type']
        verbose_name = 'Cake Customization Option'
        verbose_name_plural = 'Cake Customization Options'
    
    def __str__(self):
        return f"{self.get_customization_type_display()} - ₦{self.price_per_unit}"


class CakeSizeMultiplier(models.Model):
    """
    Store multiplier values for different cake sizes.
    The multiplier is applied to the product's design base price.
    Example: 6" = 1.0 (base), 8" = 1.3, 10" = 1.8, etc.
    """
    CAKE_SIZES = [
        ('6', '6 Inches'),
        ('8', '8 Inches'),
        ('10', '10 Inches'),
        ('12', '12 Inches'),
        ('14', '14 Inches'),
    ]
    
    size = models.CharField(
        max_length=20,
        choices=CAKE_SIZES,
        unique=True
    )
    
    multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
        help_text="Multiplier applied to product's design price. E.g., 1.5 = 50% more expensive"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['size']
        verbose_name = 'Cake Size Multiplier'
        verbose_name_plural = 'Cake Size Multipliers'
    
    def __str__(self):
        return f"{self.get_size_display()} (x{self.multiplier})"


class CakeFlavorPrice(models.Model):
    """
    Store pricing for different cake flavors.
    Some flavors might be premium and cost more.
    """
    CAKE_FLAVOURS = [
        ('Vanilla', 'Vanilla'),
        ('Chocolate', 'Chocolate'),
        ('Coconut', 'Coconut'),
        ('Marble', 'Marble'),
        ('Fruit cake', 'Fruit Cake'),
    ]
    
    flavor = models.CharField(
        max_length=50,
        choices=CAKE_FLAVOURS,
        unique=True
    )
    
    price_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.50'))],
        help_text="Multiplier applied to base price. E.g., 1.2 = 20% more expensive"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Disable to hide this flavor from customer selection"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['flavor']
        verbose_name = 'Cake Flavor Price'
        verbose_name_plural = 'Cake Flavor Prices'
    
    def __str__(self):
        return f"{self.flavor} (x{self.price_multiplier})"


# ============================================================================
# CART MODELS
# ============================================================================

class Cart(models.Model):
    """
    Shopping cart model supporting both authenticated users and guest sessions.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['user', 'is_active']]
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Guest Cart ({(self.session_key or '')[:10]}...)"
    
    @property
    def is_guest_cart(self):
        return self.user is None and self.session_key is not None
    
    @property
    def total_price(self):
        """Calculate total price including all customizations"""
        total = Decimal('0.00')
        # Use .all() to get all items and calculate in Python
        for item in self.items.all():
            total += item.total_item_price
        return total
    
    @property
    def item_count(self):
        """Get total number of items in cart"""
        total = 0
        for item in self.items.all():
            total += item.quantity
        return total
    
    @property
    def subtotal(self):
        """Alias for total_price (before delivery)"""
        return self.total_price
    
    @property
    def delivery_cost(self):
        """Placeholder for delivery cost - will be implemented with DeliveryInfo"""
        return Decimal('0.00')
    
    @property
    def grand_total(self):
        """Total price including delivery"""
        return self.total_price + self.delivery_cost

class CartItem(models.Model):
    """
    Represents a single product in the cart with all customization selections.
    Stores price snapshots at time of addition for historical accuracy.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    # Cake customization selections - Simple CharFields without hardcoded choices
    # Choices are enforced at the application level, not database level
    flavour_1 = models.CharField(
        max_length=50, 
        blank=True,
        help_text="First flavor selection"
    )
    flavour_2 = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Second flavor selection (optional)"
    )
    
    size = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Selected cake size (e.g., '6', '8', '10')"
    )
    
    colours = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Max 2 colours, e.g., 'Blue and white'"
    )
    
    # Customization quantities (how many of each add-on)
    cake_topper = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of cake toppers"
    )
    candle = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of candles"
    )
    birthday_card = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of birthday cards"
    )
    chocolate = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of chocolate boxes"
    )
    wine = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of wine bottles"
    )
    whiskey_200ml = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of whiskey bottles (200ml)"
    )
    
    additional_notes = models.TextField(
        blank=True,
        max_length=1000
    )
    
    # Pricing snapshots (stored at time of addition to preserve historical pricing)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Snapshot of product.price at time of addition (design base price for cakes)"
    )
    
    customization_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total cost of customizations for ONE cake (add-ons only)"
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    # ========================================================================
    # HELPER METHODS FOR PRICE CALCULATION
    # ========================================================================
    
    def get_size_multiplier(self):
        """
        Get the multiplier for the selected cake size.
        Returns Decimal multiplier or 1.0 if size not found.
        """
        if not self.size:
            return Decimal('1.00')
        
        try:
            size_config = CakeSizeMultiplier.objects.get(size=self.size)
            return size_config.multiplier
        except CakeSizeMultiplier.DoesNotExist:
            return Decimal('1.00')
    
    def get_flavor_multiplier(self):
        """
        Calculate the effective flavor multiplier.
        If two flavors selected, returns the average of their multipliers.
        If one flavor selected, returns that flavor's multiplier.
        If no flavor selected, returns 1.0.
        """
        multipliers = []
        
        if self.flavour_1:
            try:
                flavor = CakeFlavorPrice.objects.get(flavor=self.flavour_1, is_active=True)
                multipliers.append(flavor.price_multiplier)
            except CakeFlavorPrice.DoesNotExist:
                multipliers.append(Decimal('1.00'))
        
        if self.flavour_2:
            try:
                flavor = CakeFlavorPrice.objects.get(flavor=self.flavour_2, is_active=True)
                multipliers.append(flavor.price_multiplier)
            except CakeFlavorPrice.DoesNotExist:
                multipliers.append(Decimal('1.00'))
        
        if not multipliers:
            return Decimal('1.00')
        
        # Return average of all flavor multipliers
        return sum(multipliers, Decimal('0.00')) / len(multipliers)
    
    def calculate_addons_cost(self):
        """
        Calculate the total cost of all add-ons for ONE cake.
        This is the original customization_cost calculation.
        
        Returns: Decimal amount
        """
        total_addons = Decimal('0.00')
        
        # Get all active add-on prices in one query for efficiency
        addon_prices = {}
        try:
            addon_options = CakeCustomizationOption.objects.filter(is_active=True)
            addon_prices = {opt.customization_type: opt.price_per_unit for opt in addon_options}
        except:
            pass
        
        # Map CartItem fields to customization types
        addon_mapping = [
            ('cake_topper', 'topper'),
            ('candle', 'candle'),
            ('birthday_card', 'birthday_card'),
            ('chocolate', 'chocolate'),
            ('wine', 'wine'),
            ('whiskey_200ml', 'whiskey'),
        ]
        
        for field_name, option_type in addon_mapping:
            quantity = getattr(self, field_name, 0)
            if quantity > 0 and option_type in addon_prices:
                total_addons += addon_prices[option_type] * quantity
        
        return total_addons
    
    def calculate_total_price(self):
        """
        Calculate the complete price for ONE cake including:
        - Design base price (product.price)
        - Size multiplier
        - Flavor multiplier(s)
        - Add-ons cost
        
        Returns: Decimal amount (unit price)
        """
        if not self.product:
            return Decimal('0.00')
        
        # Get the design base price from product
        design_price = self.base_price  # This is snapshot of product.price
        
        # Get multipliers
        size_multiplier = self.get_size_multiplier()
        flavor_multiplier = self.get_flavor_multiplier()
        
        # Calculate cake base price after size and flavor adjustments
        cake_base_price = design_price * size_multiplier * flavor_multiplier
        
        # Add add-ons cost
        addons_cost = self.calculate_addons_cost()
        
        # Total for one cake
        return cake_base_price + addons_cost
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def unit_price(self):
        """Price for ONE cake including all customizations"""
        return self.calculate_total_price()
    
    @property
    def total_item_price(self):
        """Price for ALL cakes in this cart item (quantity × unit_price)"""
        return self.unit_price * self.quantity
    
    @property
    def size_multiplier_value(self):
        """Get the size multiplier value for display"""
        return self.get_size_multiplier()
    
    @property
    def flavor_multiplier_value(self):
        """Get the effective flavor multiplier for display"""
        return self.get_flavor_multiplier()
    
    # ========================================================================
    # SAVE METHOD
    # ========================================================================
    
    def save(self, *args, **kwargs):
        """
        Override save to:
        1. Calculate and store add-ons cost
        2. Validate cake requirements
        """
        # Calculate and store add-ons cost (not the full price)
        self.customization_cost = self.calculate_addons_cost()
        
        # Full validation
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def clean(self):
        """
        Custom validation for cake items.
        """
        from django.core.exceptions import ValidationError
        
        # Only validate cakes (pastries won't have these fields filled)
        if self.product.is_cake:
            # Size is required for cakes
            if not self.size:
                raise ValidationError({'size': 'Size is required for cakes.'})
            
            # At least one flavor required for cakes
            if not self.flavour_1:
                raise ValidationError({'flavour_1': 'At least one flavor is required for cakes.'})
            
            # Validate colors (max 2)
            if self.colours:
                # Split by comma or 'and'
                import re
                colour_list = re.split(r',|\sand\s', self.colours)
                colour_list = [c.strip() for c in colour_list if c.strip()]
                if len(colour_list) > 2:
                    raise ValidationError({'colours': 'Maximum 2 colours allowed. Use comma or "and" to separate.'})
        
        super().clean()
    
    # ========================================================================
    # DISPLAY & BREAKDOWN METHODS
    # ========================================================================
    
    def get_price_breakdown(self):
        """
        Return a complete breakdown of all pricing components.
        Useful for displaying itemized pricing to customer.
        
        Returns: Dictionary with full price breakdown
        """
        design_price = self.base_price
        size_multiplier = self.get_size_multiplier()
        flavor_multiplier = self.get_flavor_multiplier()
        cake_base_price = design_price * size_multiplier * flavor_multiplier
        addons_cost = self.customization_cost
        unit_price = cake_base_price + addons_cost
        
        breakdown = {
            'design_price': design_price,
            'size_multiplier': size_multiplier,
            'flavor_multiplier': flavor_multiplier,
            'cake_base_price': cake_base_price,
            'addons': self.get_addons_breakdown(),
            'addons_total': addons_cost,
            'unit_price': unit_price,
            'quantity': self.quantity,
            'item_total': unit_price * self.quantity
        }
        
        return breakdown
    
    def get_addons_breakdown(self):
        """
        Return a detailed breakdown of add-on costs.
        """
        items = []
        
        addon_mapping = [
            ('cake_topper', 'topper', 'Cake Topper'),
            ('candle', 'candle', 'Candle'),
            ('birthday_card', 'birthday_card', 'Birthday Card'),
            ('chocolate', 'chocolate', 'Chocolate Box'),
            ('wine', 'wine', 'Wine Bottle'),
            ('whiskey_200ml', 'whiskey', 'Whiskey (200ml)'),
        ]
        
        # Get all active add-on prices once
        addon_prices = {}
        try:
            addon_options = CakeCustomizationOption.objects.filter(is_active=True)
            addon_prices = {opt.customization_type: opt.price_per_unit for opt in addon_options}
        except:
            pass
        
        for field_name, option_type, display_name in addon_mapping:
            quantity = getattr(self, field_name, 0)
            
            if quantity > 0 and option_type in addon_prices:
                unit_price = addon_prices[option_type]
                total_cost = unit_price * quantity
                items.append({
                    'name': display_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_cost': total_cost
                })
        
        return items
    
    def get_customization_summary(self):
        """Get a human-readable summary of cake customizations"""
        summary_parts = []
        
        if self.flavour_1:
            summary_parts.append(f"Flavour: {self.flavour_1}")
            if self.flavour_2:
                summary_parts[-1] += f" & {self.flavour_2}"
        
        if self.size:
            # Get display name for size
            size_display = dict(CakeSizeMultiplier.CAKE_SIZES).get(self.size, f"{self.size}\"")
            summary_parts.append(f"Size: {size_display}")
        
        if self.colours:
            summary_parts.append(f"Colours: {self.colours}")
        
        # Add non-zero add-ons
        addons = []
        addon_mapping = [
            ('cake_topper', 'Topper'),
            ('candle', 'Candle'),
            ('birthday_card', 'Card'),
            ('chocolate', 'Chocolate'),
            ('wine', 'Wine'),
            ('whiskey_200ml', 'Whiskey'),
        ]
        
        for field_name, display_name in addon_mapping:
            quantity = getattr(self, field_name, 0)
            if quantity > 0:
                addons.append(f"{display_name}: {quantity}")
        
        if addons:
            summary_parts.append("Add-ons: " + ", ".join(addons))
        
        return " | ".join(summary_parts)


# ============================================================================
# DELIVERY INFO MODEL (Placeholder - Will be expanded later)
# ============================================================================

class DeliveryInfo(models.Model):
    """
    Stores delivery information for a cart.
    This is a placeholder that will be expanded in the delivery phase.
    """
    cart = models.OneToOneField(
        Cart,
        on_delete=models.CASCADE,
        related_name='delivery_info'
    )
    
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time_slot = models.CharField(max_length=50, blank=True)
    
    calculated_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    special_instructions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Delivery Information'
        verbose_name_plural = 'Delivery Information'
    
    def __str__(self):
        return f"Delivery for Cart {self.cart_id}"


# ============================================================================
# UTILITY FUNCTIONS (Cart Management)
# ============================================================================

def get_or_create_cart(request):
    """
    Get existing cart or create new one for user/guest.
    
    For authenticated users: returns their active cart
    For guests: returns cart linked to session key
    Handles merging of guest cart to user cart on login.
    
    Args:
        request: Django request object
        
    Returns:
        Cart instance
    """
    cart = None
    
    # Try to get cart for logged-in user
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        # If user has a session cart, merge it
        if 'cart_id' in request.session:
            session_cart = Cart.objects.filter(
                id=request.session['cart_id'],
                is_active=True
            ).first()
            
            if session_cart and session_cart != cart:
                cart = merge_carts(cart, session_cart)
                request.session.pop('cart_id', None)
    
    # For guests, use session
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(
                id=cart_id,
                session_key=request.session.session_key,
                is_active=True
            ).first()
    
    # Create new cart if none exists
    if not cart:
        cart = create_new_cart(request)
        request.session['cart_id'] = cart.id
    
    return cart


def create_new_cart(request):
    """
    Create a new cart for user or guest.
    
    For authenticated users: creates user-linked cart
    For guests: creates session-linked cart
    
    Args:
        request: Django request object
        
    Returns:
        Newly created Cart instance
    """
    cart = Cart()
    
    if request.user.is_authenticated:
        cart.user = request.user
    else:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        cart.session_key = request.session.session_key
    
    cart.save()
    return cart


@transaction.atomic
def merge_carts(user_cart, session_cart):
    """
    Merge guest session cart into user cart when user logs in.
    
    If user_cart is None, converts session_cart to user cart.
    Otherwise, combines items from session_cart into user_cart.
    
    Transaction is atomic to prevent race conditions.
    
    Args:
        user_cart: Cart instance for user (can be None)
        session_cart: Guest cart instance from session
        
    Returns:
        Cart instance (either merged or converted)
    """
    # If no user cart exists, convert session cart to user cart
    if not user_cart:
        session_cart.user = user_cart.user if user_cart else None
        session_cart.session_key = None
        session_cart.save()
        return session_cart
    
    # Merge items from session cart to user cart
    for session_item in session_cart.items.all():
        # Check if same product with same customization exists
        existing_item = user_cart.items.filter(
            product=session_item.product,
            flavour_1=session_item.flavour_1,
            flavour_2=session_item.flavour_2,
            size=session_item.size,
            colours=session_item.colours,
            cake_topper=session_item.cake_topper,
            candle=session_item.candle,
            birthday_card=session_item.birthday_card,
            chocolate=session_item.chocolate,
            wine=session_item.wine,
            whiskey_200ml=session_item.whiskey_200ml,
            additional_notes=session_item.additional_notes,
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += session_item.quantity
            existing_item.save()
            session_item.delete()
        else:
            # Move item to user cart
            session_item.cart = user_cart
            session_item.save()
    
    # Deactivate session cart
    session_cart.is_active = False
    session_cart.save()
    
    return user_cart


def get_cart_item_count(request):
    """
    Get total number of items in cart.
    Uses aggregate for efficiency (no N+1 query).
    
    Args:
        request: Django request object
        
    Returns:
        Integer count of total items (sum of quantities)
    """
    cart = get_or_create_cart(request)
    result = cart.items.aggregate(total=Sum('quantity'))
    return result['total'] or 0


def clear_cart(request):
    """
    Clear all items from cart.
    
    Args:
        request: Django request object
        
    Returns:
        Cart instance (now empty)
    """
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return cart