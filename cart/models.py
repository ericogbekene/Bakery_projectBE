from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from django.db import transaction
from decimal import Decimal, InvalidOperation
from django.conf import settings


# ============================================================================
# CUSTOMIZATION PRICING MODELS
# ============================================================================

class CakeCustomizationOption(models.Model):
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
        blank=True,
        help_text="Leave blank for custom addons created by admin"
    )

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name e.g. 'Balloon Pack', 'Cake Topper'"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="Auto-generated unique identifier"
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

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while CakeCustomizationOption.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']
        verbose_name = 'Cake Customization Option'
        verbose_name_plural = 'Cake Customization Options'

    def __str__(self):
        return f"{self.name} - ₦{self.price_per_unit}"
    
# ============================================================================

class CartItemAddon(models.Model):
    """
    Dynamic addons selected for a cart item.
    Links a CartItem to a CakeCustomizationOption with a quantity.
    Used for admin-created addons beyond the legacy hardcoded fields.
    """
    cart_item = models.ForeignKey(
        'CartItem',
        on_delete=models.CASCADE,
        related_name='dynamic_addons'
    )

    addon = models.ForeignKey(
        CakeCustomizationOption,
        on_delete=models.PROTECT,
        help_text="The selected customization option"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['added_at']
        unique_together = ['cart_item', 'addon']
        verbose_name = 'Cart Item Addon'
        verbose_name_plural = 'Cart Item Addons'

    def __str__(self):
        return f"{self.quantity}x {self.addon.name} for CartItem {self.cart_item_id}"

    @property
    def total_cost(self):
        return self.addon.price_per_unit * self.quantity




# CART MODELS

class CakeSizeMultiplier(models.Model):
    """
    Store multiplier values for different cake sizes.
    The multiplier is applied to the product's design base price.
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
    # Fixed: CASCADE -> SET_NULL so deleting a user doesn't delete cart history
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
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
        ordering = ['-created_at']
        # Removed unique_together — it incorrectly prevented multiple inactive carts per user
        # Active cart uniqueness is enforced at the application level in get_or_create_cart

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
        for item in self.items.all():
            total += item.total_item_price
        return total

    @property
    def item_count(self):
        """Get total number of items in cart"""
        result = self.items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    @property
    def subtotal(self):
        """Alias for total_price (before delivery)"""
        return self.total_price

    @property
    def delivery_cost(self):
        """
        Get delivery cost from DeliveryInfo if available.
        Fixed: was always returning 0.00 — now reads from calculated_fee.
        """
        try:
            return self.delivery_info.calculated_fee or Decimal('0.00')
        except DeliveryInfo.DoesNotExist:
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

    # Cake customization selections
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

    # Customization quantities
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

    # Pricing snapshots
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Snapshot of product.price at time of addition"
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
        """Get the multiplier for the selected cake size."""
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

        return sum(multipliers, Decimal('0.00')) / len(multipliers)

    def calculate_addons_cost(self):
        """Calculate the total cost of all add-ons for ONE cake.
        Includes both legacy hardcoded fields and dynamic addons.
        """
        total_addons = Decimal('0.00')

        # ── Legacy hardcoded addons ────────────────────────────────
        addon_prices = {}
        try:
            addon_options = CakeCustomizationOption.objects.filter(is_active=True)
            addon_prices = {opt.customization_type: opt.price_per_unit for opt in addon_options}
        except Exception:
            pass

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

        # ── Dynamic addons ─────────────────────────────────────────
        # Only available after the item has been saved (has a pk)
        if self.pk:
            try:
                for dynamic in self.dynamic_addons.select_related('addon').filter(
                    addon__is_active=True
                ):
                    total_addons += dynamic.addon.price_per_unit * dynamic.quantity
            except Exception:
                pass

        return total_addons


    def calculate_total_price(self):
        """
        Calculate the complete price for ONE cake including:
        - Design base price
        - Size multiplier
        - Flavor multiplier(s)
        - Add-ons cost
        """
        if not self.product:
            return Decimal('0.00')

        design_price = self.base_price
        if design_price is None:
            design_price = self.product.price if self.product else Decimal('0.00')

        if not isinstance(design_price, Decimal):
            try:
                design_price = Decimal(str(design_price))
            except (TypeError, ValueError, InvalidOperation):
                design_price = Decimal('0.00')

        size_multiplier = self.get_size_multiplier() or Decimal('1.00')
        flavor_multiplier = self.get_flavor_multiplier() or Decimal('1.00')

        try:
            cake_base_price = design_price * size_multiplier * flavor_multiplier
        except (TypeError, ValueError):
            cake_base_price = Decimal('0.00')

        addons_cost = self.calculate_addons_cost() or Decimal('0.00')

        return cake_base_price + addons_cost

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def unit_price(self):
        """Price for ONE cake including all customizations"""
        try:
            return self.calculate_total_price()
        except (TypeError, AttributeError, ValueError):
            return Decimal('0.00')

    @property
    def total_item_price(self):
        """Price for ALL cakes in this cart item (quantity × unit_price)"""
        try:
            return self.unit_price * self.quantity
        except (TypeError, AttributeError, ValueError):
            return Decimal('0.00')

    @property
    def size_multiplier_value(self):
        try:
            return self.get_size_multiplier()
        except Exception:
            return Decimal('1.00')

    @property
    def flavor_multiplier_value(self):
        try:
            return self.get_flavor_multiplier()
        except Exception:
            return Decimal('1.00')

    # ========================================================================
    # SAVE METHOD
    # ========================================================================

    # FIXED
    def save(self, *args, **kwargs):
        if self.base_price is None and self.product:
            self.base_price = self.product.price

        self.customization_cost = self.calculate_addons_cost()

        self.full_clean()   # always validate, including on first save

        super().save(*args, **kwargs)


    # ========================================================================
    # VALIDATION
    # ========================================================================

    def clean(self):
        """Custom validation for cake items."""
        from django.core.exceptions import ValidationError
        import re

        if not self.product:
            return

        if self.product.is_cake:
            if not self.size:
                raise ValidationError({'size': 'Size is required for cakes.'})

            if not self.flavour_1:
                raise ValidationError({'flavour_1': 'At least one flavor is required for cakes.'})

            if self.colours:
                colour_list = re.split(r',|\sand\s', self.colours)
                colour_list = [c.strip() for c in colour_list if c.strip()]
                if len(colour_list) > 2:
                    raise ValidationError({
                        'colours': 'Maximum 2 colours allowed. Use comma or "and" to separate.'
                    })

        super().clean()

    # ========================================================================
    # DISPLAY & BREAKDOWN METHODS
    # ========================================================================

    def get_price_breakdown(self):
        """Return a complete breakdown of all pricing components."""
        try:
            design_price = self.base_price if self.base_price is not None else Decimal('0.00')
            size_multiplier = self.get_size_multiplier()
            flavor_multiplier = self.get_flavor_multiplier()
            cake_base_price = design_price * size_multiplier * flavor_multiplier
            addons_cost = self.customization_cost or Decimal('0.00')
            unit_price = cake_base_price + addons_cost

            return {
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
        except (TypeError, AttributeError, ValueError):
            return {
                'design_price': Decimal('0.00'),
                'size_multiplier': Decimal('1.00'),
                'flavor_multiplier': Decimal('1.00'),
                'cake_base_price': Decimal('0.00'),
                'addons': [],
                'addons_total': Decimal('0.00'),
                'unit_price': Decimal('0.00'),
                'quantity': self.quantity,
                'item_total': Decimal('0.00')
            }

    def get_addons_breakdown(self):
        """Return a detailed breakdown of add-on costs."""
        items = []

        addon_mapping = [
            ('cake_topper', 'topper', 'Cake Topper'),
            ('candle', 'candle', 'Candle'),
            ('birthday_card', 'birthday_card', 'Birthday Card'),
            ('chocolate', 'chocolate', 'Chocolate Box'),
            ('wine', 'wine', 'Wine Bottle'),
            ('whiskey_200ml', 'whiskey', 'Whiskey (200ml)'),
        ]

        addon_prices = {}
        try:
            addon_options = CakeCustomizationOption.objects.filter(is_active=True)
            addon_prices = {opt.customization_type: opt.price_per_unit for opt in addon_options}
        except Exception:
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
            try:
                size_display = dict(CakeSizeMultiplier.CAKE_SIZES).get(self.size, f"{self.size}\"")
            except Exception:
                size_display = f"{self.size}\""
            summary_parts.append(f"Size: {size_display}")

        if self.colours:
            summary_parts.append(f"Colours: {self.colours}")

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
# DELIVERY INFO MODEL
# ============================================================================

class DeliveryInfo(models.Model):
    """
    Stores delivery information for a cart.
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