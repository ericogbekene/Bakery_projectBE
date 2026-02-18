from rest_framework import serializers
from delivery.models import (
    DeliveryZone, DeliveryPricingRule, 
    DeliverySchedule, DeliveryException, DeliveryService
)
from datetime import date
from decimal import Decimal


class DeliveryZoneSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery zones.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    area_list = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'code', 'description', 'areas', 'area_list',
            'base_fee', 'free_delivery_threshold', 'estimated_delivery_days',
            'rush_delivery_available', 'rush_delivery_premium',
            'status', 'status_display', 'display_order'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_area_list(self, obj):
        """Return areas as a list."""
        return obj.area_list


class DeliveryZoneListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing delivery zones.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'code', 'base_fee', 
            'free_delivery_threshold', 'estimated_delivery_days',
            'status', 'status_display'
        ]


class DeliveryPricingRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery pricing rules.
    """
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    
    class Meta:
        model = DeliveryPricingRule
        fields = [
            'id', 'name', 'rule_type', 'rule_type_display',
            'zone', 'zone_name', 'min_value', 'max_value',
            'fee_type', 'fee_type_display', 'fee_value',
            'applies_to_rush', 'applies_to_regular',
            'valid_from', 'valid_until', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeliveryScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery schedules.
    """
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    slots_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DeliverySchedule
        fields = [
            'id', 'zone', 'zone_name', 'day_of_week', 'day_display',
            'time_slot_name', 'start_time', 'end_time',
            'max_orders_per_slot', 'current_orders',
            'is_available', 'slots_remaining', 'is_active'
        ]


class DeliveryExceptionSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery exceptions.
    """
    exception_type_display = serializers.CharField(source='get_exception_type_display', read_only=True)
    zone_names = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryException
        fields = [
            'id', 'date', 'exception_type', 'exception_type_display',
            'title', 'description', 'zones', 'zone_names',
            'delivery_available', 'modified_fee', 'modified_schedule'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_zone_names(self, obj):
        """Return list of zone names."""
        return [zone.name for zone in obj.zones.all()]


class CalculateDeliveryFeeSerializer(serializers.Serializer):
    """
    Serializer for calculating delivery fee.
    """
    city = serializers.CharField(max_length=100)
    order_total = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        default=Decimal('0.00')
    )
    is_rush = serializers.BooleanField(default=False)
    
    def validate_city(self, value):
        """Validate that city is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("City is required.")
        return value.strip()


class DeliveryFeeResponseSerializer(serializers.Serializer):
    """
    Serializer for delivery fee response.
    """
    fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    zone = DeliveryZoneListSerializer(read_only=True)
    zone_name = serializers.CharField()
    zone_code = serializers.CharField()
    available = serializers.BooleanField()
    estimated_days = serializers.IntegerField()
    rush_available = serializers.BooleanField()
    rush_premium = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    free_delivery_threshold = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    message = serializers.CharField()


class AvailableDatesSerializer(serializers.Serializer):
    """
    Serializer for available delivery dates.
    """
    zone_id = serializers.IntegerField(required=False, allow_null=True)
    days_ahead = serializers.IntegerField(default=14, min_value=1, max_value=60)


class DateSlotSerializer(serializers.Serializer):
    """
    Serializer for a single date slot.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    start = serializers.CharField()
    end = serializers.CharField()
    slots_remaining = serializers.IntegerField()


class AvailableDateSerializer(serializers.Serializer):
    """
    Serializer for an available delivery date.
    """
    date = serializers.DateField()
    date_str = serializers.CharField()
    day_name = serializers.CharField()
    slots = DateSlotSerializer(many=True)
    modified_schedule = serializers.CharField(allow_null=True)


class ValidateAddressSerializer(serializers.Serializer):
    """
    Serializer for validating delivery address.
    """
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)


class AddressValidationResponseSerializer(serializers.Serializer):
    """
    Serializer for address validation response.
    """
    valid = serializers.BooleanField()
    zone = DeliveryZoneListSerializer(allow_null=True)
    message = serializers.CharField()
    suggested_cities = serializers.ListField(child=serializers.CharField(), required=False)