from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
from decimal import Decimal
from delivery.constants import NIGERIA_STATES


# ============================================================================
# DELIVERY ZONE MODEL
# ============================================================================

class DeliveryZone(models.Model):
    """
    Admin-managed delivery fee per state.
    Only states with an active zone here are offered as delivery
    options on the frontend — everywhere else, pickup is the only choice.
    """

    ZONE_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('temporary', 'Temporarily Unavailable'),
    ]

    state = models.CharField(
        max_length=20,
        choices=NIGERIA_STATES,
        unique=True,
        help_text="State this fee applies to"
    )

    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Delivery fee for this state"
    )

    status = models.CharField(
        max_length=20,
        choices=ZONE_STATUS,
        default='active',
        db_index=True,
        help_text="Current availability of this zone"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['state']
        verbose_name = 'Delivery Zone'
        verbose_name_plural = 'Delivery Zones'
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_state_display()} - ₦{self.fee:,.0f}"

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
        return f"{self.zone.get_state_display()} - {self.get_day_of_week_display()} {self.time_slot_name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
   
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
    Service class for delivery fee calculation.
    """

    @staticmethod
    def calculate_delivery_fee_by_state(state, is_pickup=False):
        """
        Calculate delivery fee based on state.
        Pickup orders always return a fee of 0 with no zone lookup.

        Args:
            state: State code (must match NIGERIA_STATES choices)
            is_pickup: Whether this is a pickup order

        Returns:
            Dictionary with fee, available, and message
        """
        if is_pickup:
            return {
                'fee': Decimal('0.00'),
                'available': True,
                'message': 'Pickup selected — no delivery fee applies.'
            }

        try:
            zone = DeliveryZone.objects.get(state=state, status='active')
            return {
                'fee': zone.fee,
                'available': True,
                'message': 'Delivery available.'
            }
        except DeliveryZone.DoesNotExist:
            return {
                'fee': Decimal('0.00'),
                'available': False,
                'message': 'Delivery not available to this state.'
            }

    @staticmethod
    def get_available_dates(zone=None, days_ahead=14):
        """
        Get available delivery dates. Unchanged from previous implementation —
        still relevant for delivery scheduling, independent of fee logic.
        """
        from datetime import timedelta

        available_dates = []
        today = now().date()

        for i in range(1, days_ahead + 1):
            date = today + timedelta(days=i)

            exceptions = DeliveryException.objects.filter(date=date)
            if zone:
                exceptions = exceptions.filter(
                    models.Q(zones=zone) | models.Q(zones__isnull=True)
                )
            else:
                exceptions = exceptions.filter(zones__isnull=True)

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
                    continue

            available_dates.append({
                'date': date,
                'date_str': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%A'),
                'slots': slots,
                'modified_schedule': modified_schedule
            })

        return available_dates