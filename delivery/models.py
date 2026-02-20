from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
from decimal import Decimal


# ============================================================================
# DELIVERY ZONE MODEL
# ============================================================================

class DeliveryZone(models.Model):
    """
    Defines delivery zones and their base characteristics.
    Each zone has a name, areas covered, and base delivery fee.
    """
    
    ZONE_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('temporary', 'Temporarily Unavailable'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Zone name (e.g., 'Zone A - Jahi', 'Zone B - Wuse')"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short code for the zone (e.g., 'JAH', 'WUS', 'MAI')"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Description of areas covered by this zone"
    )
    
    # Areas covered (comma-separated or JSON)
    areas = models.TextField(
        help_text="List of areas/neighborhoods in this zone, separated by commas"
    )
    
    # Base delivery fee
    base_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Base delivery fee for this zone"
    )
    
    # Free delivery threshold
    free_delivery_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Order amount for free delivery (null = no free delivery)"
    )
    
    # Estimated delivery time
    estimated_delivery_days = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Estimated delivery days for this zone"
    )
    
    # Rush delivery premium (if offered)
    rush_delivery_available = models.BooleanField(
        default=False,
        help_text="Whether rush/same-day delivery is available for this zone"
    )
    
    rush_delivery_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Additional fee for rush delivery"
    )
    
    # Zone status
    status = models.CharField(
        max_length=20,
        choices=ZONE_STATUS,
        default='active',
        db_index=True,
        help_text="Current availability of this zone"
    )
    
    # Display order
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order to display zones in dropdowns"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Delivery Zone'
        verbose_name_plural = 'Delivery Zones'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - ₦{self.base_fee:,.0f}"
    
    @property
    def area_list(self):
        """Return areas as a list"""
        return [area.strip() for area in self.areas.split(',') if area.strip()]
    
    def get_delivery_fee(self, order_total=None):
        """
        Calculate delivery fee based on order total.
        Returns 0 if order meets free delivery threshold.
        """
        if order_total and self.free_delivery_threshold:
            if order_total >= self.free_delivery_threshold:
                return Decimal('0.00')
        return self.base_fee


# ============================================================================
# DELIVERY PRICING RULES MODEL
# ============================================================================

class DeliveryPricingRule(models.Model):
    """
    Additional pricing rules for delivery.
    e.g., distance-based fees, special event pricing, etc.
    """
    
    RULE_TYPES = [
        ('distance', 'Distance-based'),
        ('weight', 'Weight-based'),
        ('special', 'Special Event'),
        ('promotion', 'Promotional'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Rule name"
    )
    
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPES,
        db_index=True,
        help_text="Type of pricing rule"
    )
    
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        related_name='pricing_rules',
        null=True,
        blank=True,
        help_text="Apply to specific zone (null = all zones)"
    )
    
    # Condition
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum value (distance in km, weight in kg, etc.)"
    )
    
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum value"
    )
    
    # Fee calculation
    fee_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixed Amount'),
            ('percentage', 'Percentage of Order'),
            ('per_unit', 'Per Unit (km/kg)'),
        ],
        default='fixed',
        help_text="How to calculate the fee"
    )
    
    fee_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Fee amount, percentage, or rate per unit"
    )
    
    # Applicability
    applies_to_rush = models.BooleanField(
        default=True,
        help_text="Whether this rule applies to rush deliveries"
    )
    
    applies_to_regular = models.BooleanField(
        default=True,
        help_text="Whether this rule applies to regular deliveries"
    )
    
    # Date restrictions (for special events)
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Rule valid from this date"
    )
    
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Rule valid until this date"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rule is active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['rule_type', 'name']
        verbose_name = 'Delivery Pricing Rule'
        verbose_name_plural = 'Delivery Pricing Rules'
    
    def __str__(self):
        return f"{self.name} - {self.get_rule_type_display()}"
    
    def is_valid(self, check_date=None):
        """Check if rule is currently valid based on dates"""
        if not self.is_active:
            return False
        
        if check_date is None:
            check_date = now()
        
        if self.valid_from and check_date < self.valid_from:
            return False
        
        if self.valid_until and check_date > self.valid_until:
            return False
        
        return True


# ============================================================================
# DELIVERY SCHEDULE MODEL
# ============================================================================

class DeliverySchedule(models.Model):
    """
    Available delivery time slots and schedules.
    """
    
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Zone this schedule applies to"
    )
    
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        help_text="Day of week"
    )
    
    # Time slots
    time_slot_name = models.CharField(
        max_length=50,
        help_text="e.g., 'Morning', 'Afternoon', 'Evening'"
    )
    
    start_time = models.TimeField(
        help_text="Slot start time"
    )
    
    end_time = models.TimeField(
        help_text="Slot end time"
    )
    
    # Capacity management
    max_orders_per_slot = models.PositiveIntegerField(
        default=10,
        help_text="Maximum orders per time slot"
    )
    
    current_orders = models.PositiveIntegerField(
        default=0,
        help_text="Current number of orders for this slot"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this time slot is available"
    )
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['zone', 'day_of_week', 'time_slot_name']
        verbose_name = 'Delivery Schedule'
        verbose_name_plural = 'Delivery Schedules'
    
    def __str__(self):
        return f"{self.zone.name} - {self.get_day_of_week_display()} {self.time_slot_name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
    
    @property
    def is_available(self):
        """Check if slot has capacity"""
        return self.is_active and self.current_orders < self.max_orders_per_slot
    
    @property
    def slots_remaining(self):
        """Get remaining slots"""
        return max(0, self.max_orders_per_slot - self.current_orders)


# ============================================================================
# DELIVERY EXCEPTION MODEL (Holidays, Closures)
# ============================================================================

class DeliveryException(models.Model):
    """
    Special dates when delivery is unavailable or modified.
    e.g., Public holidays, bad weather, etc.
    """
    
    EXCEPTION_TYPES = [
        ('holiday', 'Public Holiday'),
        ('closure', 'Temporary Closure'),
        ('weather', 'Weather Issue'),
        ('event', 'Special Event'),
        ('maintenance', 'System Maintenance'),
    ]
    
    date = models.DateField(
        help_text="Date of exception"
    )
    
    exception_type = models.CharField(
        max_length=20,
        choices=EXCEPTION_TYPES,
        help_text="Type of exception"
    )
    
    title = models.CharField(
        max_length=100,
        help_text="Short title (e.g., 'Christmas Day')"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed description"
    )
    
    # Affected zones (null = all zones)
    zones = models.ManyToManyField(
        DeliveryZone,
        blank=True,
        related_name='exceptions',
        help_text="Affected zones (leave empty for all zones)"
    )
    
    # Delivery modifications
    delivery_available = models.BooleanField(
        default=False,
        help_text="Is delivery available on this date?"
    )
    
    modified_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Modified delivery fee for this date"
    )
    
    modified_schedule = models.CharField(
        max_length=100,
        blank=True,
        help_text="Modified schedule (e.g., '10am-2pm only')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date']
        unique_together = ['date', 'title']
        verbose_name = 'Delivery Exception'
        verbose_name_plural = 'Delivery Exceptions'
    
    def __str__(self):
        return f"{self.date} - {self.title}"


# ============================================================================
# DELIVERY SERVICE FUNCTIONS
# ============================================================================

class DeliveryService:
    """
    Service class for delivery calculations and operations.
    """
    
    @staticmethod
    def get_zone_from_city(city):
        """
        Determine delivery zone from city/area name.
        Returns DeliveryZone object or None.
        """
        city_lower = city.lower().strip()
        
        # Search for zone containing this city/area
        for zone in DeliveryZone.objects.filter(status='active'):
            for area in zone.area_list:
                if area.lower() in city_lower or city_lower in area.lower():
                    return zone
        
        return None
    
    @staticmethod
    def calculate_delivery_fee(city, order_total=None, is_rush=False):
        """
        Calculate delivery fee based on city and order total.
        
        Args:
            city: City/area name
            order_total: Order subtotal (for free delivery threshold)
            is_rush: Whether this is a rush delivery
        
        Returns:
            Dictionary with fee, zone, and details
        """
        zone = DeliveryService.get_zone_from_city(city)
        
        if not zone:
            return {
                'fee': Decimal('0.00'),
                'zone': None,
                'available': False,
                'message': 'Delivery not available to this location'
            }
        
        # Check if zone is active
        if zone.status != 'active':
            return {
                'fee': Decimal('0.00'),
                'zone': zone,
                'available': False,
                'message': f'Delivery temporarily unavailable to {zone.name}'
            }
        
        # Calculate base fee
        fee = zone.get_delivery_fee(order_total)
        
        # Add rush premium if applicable
        if is_rush and zone.rush_delivery_available:
            fee += zone.rush_delivery_premium
        
        # Apply additional pricing rules
        for rule in DeliveryPricingRule.objects.filter(
            models.Q(zone=zone) | models.Q(zone__isnull=True),
            is_active=True
        ):
            if rule.is_valid():
                # Apply rule based on type
                if rule.rule_type == 'distance':
                    # Would need distance calculation
                    pass
                elif rule.rule_type == 'special':
                    if is_rush and not rule.applies_to_rush:
                        continue
                    if not is_rush and not rule.applies_to_regular:
                        continue
                    
                    if rule.fee_type == 'fixed':
                        fee += rule.fee_value
                    elif rule.fee_type == 'percentage' and order_total:
                        fee += (order_total * rule.fee_value / 100)
        
        return {
            'fee': fee,
            'zone': zone,
            'zone_name': zone.name,
            'zone_code': zone.code,
            'available': True,
            'estimated_days': zone.estimated_delivery_days,
            'rush_available': zone.rush_delivery_available,
            'rush_premium': zone.rush_delivery_premium if is_rush else None,
            'free_delivery_threshold': zone.free_delivery_threshold,
            'message': 'Delivery available'
        }
    
    @staticmethod
    def get_available_dates(zone=None, days_ahead=14):
        """
        Get available delivery dates.
        Excludes exceptions and fully booked slots.
        """
        from datetime import datetime, timedelta
        
        available_dates = []
        today = now().date()
        
        for i in range(1, days_ahead + 1):
            date = today + timedelta(days=i)
            
            # Check for exceptions
            exceptions = DeliveryException.objects.filter(date=date)
            if zone:
                exceptions = exceptions.filter(
                    models.Q(zones=zone) | models.Q(zones__isnull=True)
                )
            else:
                exceptions = exceptions.filter(zones__isnull=True)
            
            # Skip if delivery not available
            skip_date = False
            modified_schedule = None
            
            for exception in exceptions:
                if not exception.delivery_available:
                    skip_date = True
                    break
                if exception.modified_schedule:
                    modified_schedule = exception.modified_schedule
            
            if skip_date:
                continue
            
            # Get available time slots
            slots = []
            if zone:
                day_slots = DeliverySchedule.objects.filter(
                    zone=zone,
                    day_of_week=date.weekday(),
                    is_active=True
                )
                
                for slot in day_slots:
                    if slot.is_available:
                        slots.append({
                            'id': slot.id,
                            'name': slot.time_slot_name,
                            'start': slot.start_time.strftime('%H:%M'),
                            'end': slot.end_time.strftime('%H:%M'),
                            'slots_remaining': slot.slots_remaining
                        })
                
                if not slots:
                    continue  # No available slots this day
            
            available_dates.append({
                'date': date,
                'date_str': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%A'),
                'slots': slots,
                'modified_schedule': modified_schedule
            })
        
        return available_dates