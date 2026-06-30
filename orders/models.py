from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from decimal import Decimal
import uuid
from django.conf import settings  # ✅ Import settings for AUTH_USER_MODEL

# ============================================================================
# IMPORT FIXED - Circular import resolved
# ============================================================================
from cart.models import Cart  # ✅ Correct import from cart app


# ============================================================================
# ORDER STATUS CHOICES
# ============================================================================

ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('processing', 'Processing'),
    ('ready', 'Ready for Pickup/Delivery'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
]

PAYMENT_METHOD_CHOICES = [
    ('credit_card', 'Credit Card'),
    ('debit_card', 'Debit Card'),
    ('bank_transfer', 'Bank Transfer'),
    ('cash', 'Cash on Delivery'),
]


# ============================================================================
# ORDER MODEL (UPDATED FOR PAYSTACK)
# ============================================================================

class Order(models.Model):
    """
    Main Order model that stores customer orders.
    Links to Cart and tracks order status and payment.
    Payment method is Paystack only.
    """
    
    # Order Identification
    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Unique order identifier (ORD-YYYYMMDD-UUID8)"
    )
    
    # Customer Information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Customer user account (null for guest)"
    )
    
    guest_email = models.EmailField(
        blank=True,
        help_text="Email for guest checkout"
    )
    
    guest_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone for guest checkout"
    )
    
    # Cart Reference
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Original cart (for reference, cart becomes inactive after order)"
    )
    
    # Customer Contact (Snapshot at order time)
    customer_name = models.CharField(
        max_length=100,
        help_text="Full name for order/delivery"
    )
    
    customer_email = models.EmailField(
        help_text="Email for order confirmation and updates"
    )
    
    customer_phone = models.CharField(
        max_length=20,
        help_text="Phone number for order updates"
    )
    
    # Pricing Information (Simplified - no tax/discount)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Subtotal from cart (items only)"
    )
    
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Delivery fee calculated at checkout"
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Final total to be paid (subtotal + delivery_fee)"
    )
    
    # Order Status
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Current order status"
    )
    
    # Payment Information - Updated for Paystack
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Payment status"
    )
    
    # Payment method is always Paystack
    payment_method = models.CharField(
        max_length=20,
        default='paystack',
        editable=False,
        help_text="Payment method (always Paystack)"
    )
    
    # Paystack specific fields
    paystack_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Paystack transaction ID"
    )
    
    paystack_reference = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Paystack payment reference"
    )
    
    paystack_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Full Paystack response for reference"
    )
    
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was received"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When order was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update time"
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was confirmed"
    )
    
    processing_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order started processing"
    )
    
    ready_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was marked ready"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was completed"
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was cancelled"
    )
    
    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation"
    )
    
    # Admin Notes
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for staff"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['paystack_transaction_id']),
            models.Index(fields=['paystack_reference']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        """Generate order number on creation"""
        if not self.order_number:
            # Generate unique order number: ORD-20260213-ABC12345
            date_str = now().strftime('%Y%m%d')
            short_uuid = str(uuid.uuid4())[:8].upper()
            self.order_number = f"ORD-{date_str}-{short_uuid}"
        
        # Ensure payment_method is always paystack
        self.payment_method = 'paystack'
        
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_confirmed(self):
        return self.status == 'confirmed'
    
    @property
    def is_processing(self):
        return self.status == 'processing'
    
    @property
    def is_ready(self):
        return self.status == 'ready'
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_cancelled(self):
        return self.status == 'cancelled'
    
    @property
    def is_paid(self):
        return self.payment_status == 'paid'
    
    @property
    def paystack_payload(self):
        """
        Generate Paystack payment payload for this order.
        Useful when redirecting to Paystack payment page.
        """
        return {
            'reference': self.paystack_reference or self.order_number,
            'amount': int(self.total_amount * 100),  # Convert to kobo/cents
            'currency': 'NGN',
            'callback_url': '/payment/callback/',  # Configure this
            'customer': {
                'email': self.customer_email,
                'name': self.customer_name,
                'phone': self.customer_phone,
            },
            'metadata': {
                'order_number': self.order_number,
                'order_id': self.id,
            },
            'customizations': {
                'title': 'M&C Bakery Order',
                'description': f'Order #{self.order_number}',
            }
        }
    
    def get_status_display_color(self):
        """Get color for status display (for admin UI)"""
        colors = {
            'pending': '#ffc107',      # Yellow
            'confirmed': '#17a2b8',    # Blue
            'processing': '#007bff',   # Dark Blue
            'ready': '#28a745',        # Green
            'completed': '#6c757d',    # Gray
            'cancelled': '#dc3545',    # Red
        }
        return colors.get(self.status, '#ffffff')
    
    def get_payment_status_color(self):
        """Get color for payment status display"""
        colors = {
            'pending': '#ffc107',      # Yellow
            'paid': '#28a745',         # Green
            'failed': '#dc3545',       # Red
            'refunded': '#6c757d',     # Gray
        }
        return colors.get(self.payment_status, '#ffffff')
    
    def update_total_cost(self):
        """
        Recalculate order total from all order items.
        Called by signals when OrderItems are added/updated/deleted.
        """
        from django.db.models import Sum
        items_total = self.items.aggregate(
            total=Sum('item_total')
        )['total'] or Decimal('0.00')
    
        self.subtotal = items_total
        self.total_amount = self.subtotal + self.delivery_fee
        self.save(update_fields=['subtotal', 'total_amount'])
    
    def update_status(self, new_status, user=None, reason=""):
        """
        Update order status and automatically set timestamp.
        Creates OrderHistory entry for audit trail.
        """
        old_status = self.status
        self.status = new_status
        
        # Set appropriate timestamp
        if new_status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = now()
        elif new_status == 'processing' and not self.processing_at:
            self.processing_at = now()
        elif new_status == 'ready' and not self.ready_at:
            self.ready_at = now()
        elif new_status == 'completed' and not self.completed_at:
            self.completed_at = now()
        elif new_status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = now()
            self.cancellation_reason = reason
        
        self.save()
        
        # Create history entry
        OrderHistory.objects.create(
            order=self,
            action='status_changed',
            description=f"Status changed from {old_status} to {new_status}",
            changed_by=user,
            old_value=old_status,
            new_value=new_status
        )
    
    def update_payment(self, payment_status, transaction_id=None, reference=None, response_data=None):
        """
        Update payment information after Paystack callback.
        """
        old_status = self.payment_status
        self.payment_status = payment_status
        
        if transaction_id:
            self.paystack_transaction_id = transaction_id
        
        if reference:
            self.paystack_reference = reference
        
        if response_data:
            self.paystack_response = response_data
        
        if payment_status == 'paid' and not self.payment_date:
            self.payment_date = now()
        
        self.save()
        
        # Create history entry
        OrderHistory.objects.create(
            order=self,
            action='payment_received' if payment_status == 'paid' else 'status_changed',
            description=f"Payment status changed from {old_status} to {payment_status}",
            old_value=old_status,
            new_value=payment_status
        )


# ============================================================================
# ORDER DELIVERY MODEL (SEPARATE, MATCHES CART PATTERN)
# ============================================================================

class OrderDelivery(models.Model):
    """
    Separate model for delivery information.
    Snapshot of delivery details at order time.
    Matches the pattern used in Cart app with DeliveryInfo.
    """
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery',
        help_text="Related order"
    )
    
    # Delivery Address
    address = models.TextField(
        help_text="Full delivery address"
    )
    
    city = models.CharField(
        max_length=100,
        help_text="City/Area for delivery zone calculation"
    )
    
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text="State/Province"
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Postal/ZIP code"
    )
    
    # Delivery Schedule
    delivery_date = models.DateField(
        help_text="Requested delivery date"
    )
    
    delivery_time_slot = models.CharField(
        max_length=50,
        blank=True,
        help_text="Preferred time slot (e.g., '10am-12pm')"
    )
    
    # Delivery Pricing Snapshot
    delivery_zone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Delivery zone used for fee calculation"
    )
    
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Delivery fee charged"
    )
    
    # Special Instructions
    special_instructions = models.TextField(
        blank=True,
        max_length=1000,
        help_text="Special instructions for delivery"
    )
    
    # Delivery Status (separate from order status)
    is_delivered = models.BooleanField(
        default=False,
        help_text="Whether delivery has been completed"
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When delivery was completed"
    )
    
    delivery_notes = models.TextField(
        blank=True,
        help_text="Notes from delivery person"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order Delivery'
        verbose_name_plural = 'Order Deliveries'
    
    def __str__(self):
        return f"Delivery for Order #{self.order.order_number} - {self.city}"
    
    def mark_delivered(self):
        """Mark delivery as completed"""
        self.is_delivered = True
        self.delivered_at = now()
        self.save()
        
        # Update order status if not already completed
        if self.order.status != 'completed':
            self.order.update_status('completed')


# ============================================================================
# ORDER ITEM MODEL
# ============================================================================

class OrderItem(models.Model):
    """
    Individual items in an order.
    Snapshot of CartItem at time of order creation.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent order"
    )
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Product ordered"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of cakes"
    )
    
    # Customization Details (Snapshot)
    flavour_1 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="First flavor chosen"
    )
    
    flavour_2 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Second flavor chosen"
    )
    
    size = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Cake size (e.g., 6, 8, 10, 12, 14 inches)"
    )
    
    colours = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Colors/decorations"
    )
    
    # Add-ons (Snapshot)
    cake_topper = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Number of toppers"
    )
    
    candle = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Number of candles"
    )
    
    birthday_card = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Number of cards"
    )
    
    chocolate = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Number of chocolate boxes"
    )
    
    wine = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Number of wine bottles"
    )
    
    whiskey_200ml = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Number of whiskey bottles"
    )
    
    additional_notes = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="Special instructions for this item"
    )
    
    # Pricing Snapshot (Frozen at order time)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Base price per cake (product.price snapshot)"
    )
    
    customization_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost of customizations per cake"
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Price per cake (base + customizations)"
    )
    
    item_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total for this line item (unit_price × quantity)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When item was added to order"
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
    
    def __str__(self):
        product_name = self.product.name if self.product else 'Unknown Product'
        return f"{self.quantity}x {product_name} - Order #{self.order.order_number}"
    
    def save(self, *args, **kwargs):
        """Calculate totals on save"""
        self.unit_price = self.base_price + self.customization_cost
        self.item_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Get total price for this item (alias)"""
        return self.item_total
    
    def get_customization_summary(self):
        """Get summary of customizations"""
        summary = []
        if self.flavour_1:
            summary.append(f"Flavour 1: {self.flavour_1}")
        if self.flavour_2:
            summary.append(f"Flavour 2: {self.flavour_2}")
        if self.size:
            size_display = f"{self.size}\""
            summary.append(f"Size: {size_display}")
        if self.colours:
            summary.append(f"Colours: {self.colours}")
        return ", ".join(summary) if summary else "No customization"
    
    def get_addons_summary(self):
        """Get summary of add-ons"""
        addons = []
        if self.cake_topper:
            addons.append(f"{self.cake_topper} topper(s)")
        if self.candle:
            addons.append(f"{self.candle} candle(s)")
        if self.birthday_card:
            addons.append(f"{self.birthday_card} card(s)")
        if self.chocolate:
            addons.append(f"{self.chocolate} chocolate")
        if self.wine:
            addons.append(f"{self.wine} wine")
        if self.whiskey_200ml:
            addons.append(f"{self.whiskey_200ml} whiskey")
        return ", ".join(addons) if addons else "No add-ons"


# ============================================================================
# ORDER HISTORY MODEL (NO CHANGES NEEDED)
# ============================================================================

class OrderHistory(models.Model):
    """
    Track status changes and events for an order.
    Useful for audit trail and customer communication.
    """
    
    ACTION_CHOICES = [
        ('created', 'Order Created'),
        ('confirmed', 'Order Confirmed'),
        ('payment_received', 'Payment Received'),
        ('processing', 'Processing Started'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Order Completed'),
        ('cancelled', 'Order Cancelled'),
        ('refunded', 'Refunded'),
        ('note_added', 'Note Added'),
        ('status_changed', 'Status Changed'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Related order"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Action taken"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Details about the action"
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_actions',
        help_text="Staff member who made the change"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When action occurred"
    )
    
    old_value = models.CharField(
        max_length=100,
        blank=True,
        help_text="Previous value (for status changes)"
    )
    
    new_value = models.CharField(
        max_length=100,
        blank=True,
        help_text="New value (for status changes)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Order History'
        verbose_name_plural = 'Order Histories'
        indexes = [
            models.Index(fields=['order', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - Order #{self.order.order_number} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# ============================================================================
# ORDER PAYMENT MODEL (NO CHANGES NEEDED)
# ============================================================================

class OrderPayment(models.Model):
    """
    Track payment transactions for an order.
    Useful for reconciliation and payment history.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Related order"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Payment amount"
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Payment method used"
    )
    
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Payment gateway transaction ID"
    )
    
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text="Payment status"
    )
    
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank/Payment reference"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Payment notes"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When payment was initiated"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was processed"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Payment'
        verbose_name_plural = 'Order Payments'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['order', '-created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - ₦{self.amount} - Order #{self.order.order_number}"


# ============================================================================
# ORDER SERVICE FUNCTIONS
# ============================================================================

def create_order_from_cart(cart, customer_data, delivery_data, payment_method=''):
    """
    Create an order from a cart with all necessary snapshots.
    
    Args:
        cart: Cart instance to convert
        customer_data: Dict with 'name', 'email', 'phone'
        delivery_data: Dict with address, city, date, etc.
        payment_method: Optional payment method
    
    Returns:
        Order instance
    """
    from django.db import transaction
    
    with transaction.atomic():
        # 1. Create the Order
        order = Order.objects.create(
            user=cart.user,
            guest_email=customer_data.get('email', '') if not cart.user else '',
            guest_phone=customer_data.get('phone', '') if not cart.user else '',
            customer_name=customer_data['name'],
            customer_email=customer_data['email'],
            customer_phone=customer_data['phone'],
            cart=cart,
            subtotal=cart.subtotal,
            delivery_fee=delivery_data.get('delivery_fee', Decimal('0.00')),
            total_amount=cart.subtotal + delivery_data.get('delivery_fee', Decimal('0.00')),
            payment_method=payment_method or 'paystack',
            status='pending',
            payment_status='pending'
        )
        
        # 2. Create Order Items from Cart Items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                flavour_1=cart_item.flavour_1,
                flavour_2=cart_item.flavour_2,
                size=cart_item.size,
                colours=cart_item.colours,
                cake_topper=cart_item.cake_topper,
                candle=cart_item.candle,
                birthday_card=cart_item.birthday_card,
                chocolate=cart_item.chocolate,
                wine=cart_item.wine,
                whiskey_200ml=cart_item.whiskey_200ml,
                additional_notes=cart_item.additional_notes,
                base_price=cart_item.base_price,
                customization_cost=cart_item.customization_cost,
                unit_price=cart_item.unit_price,
                item_total=cart_item.total_item_price
            )
        
        # 3. Create Order Delivery
        OrderDelivery.objects.create(
            order=order,
            address=delivery_data['address'],
            city=delivery_data['city'],
            state=delivery_data.get('state', ''),
            postal_code=delivery_data.get('postal_code', ''),
            delivery_date=delivery_data['delivery_date'],
            delivery_time_slot=delivery_data.get('delivery_time_slot', ''),
            delivery_zone=delivery_data.get('delivery_zone', ''),
            delivery_fee=delivery_data.get('delivery_fee', Decimal('0.00')),
            special_instructions=delivery_data.get('special_instructions', '')
        )
        
        # 4. Create Order History entry
        OrderHistory.objects.create(
            order=order,
            action='created',
            description=f"Order created from cart #{cart.id}",
            changed_by=cart.user
        )
        
        # Cart remains active until payment is confirmed.
        # Deactivation happens in payment/views.py after Paystack confirms payment.
        return order