from rest_framework import serializers
from delivery.models import (
    DeliveryZone, DeliverySchedule, DeliveryException, DeliveryService
)
from decimal import Decimal


class DeliveryZoneSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery zones (admin use — full detail).
    """
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'state', 'state_display', 'fee',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeliveryZoneListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing active delivery zones.
    Used to populate the frontend state dropdown at checkout.
    """
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = DeliveryZone
        fields = ['id', 'state', 'state_display', 'fee']


class DeliveryScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery schedules.
    """
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    zone_state = serializers.CharField(source='zone.get_state_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    slots_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeliverySchedule
        fields = [
            'id', 'zone', 'zone_state', 'day_of_week', 'day_display',
            'time_slot_name', 'start_time', 'end_time',
            'max_orders_per_slot', 'current_orders',
            'is_available', 'slots_remaining', 'is_active'
        ]


class DeliveryExceptionSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery exceptions.
    """
    exception_type_display = serializers.CharField(source='get_exception_type_display', read_only=True)
    zone_states = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryException
        fields = [
            'id', 'date', 'exception_type', 'exception_type_display',
            'title', 'description', 'zones', 'zone_states',
            'delivery_available', 'modified_fee', 'modified_schedule'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_zone_states(self, obj):
        """Return list of zone state display names."""
        return [zone.get_state_display() for zone in obj.zones.all()]


class CalculateDeliveryFeeSerializer(serializers.Serializer):
    """
    Serializer for calculating delivery fee by state.
    """
    state = serializers.CharField(max_length=20)
    is_pickup = serializers.BooleanField(default=False)

    def validate_state(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("State is required.")
        return value.strip().lower()


class DeliveryFeeResponseSerializer(serializers.Serializer):
    """
    Serializer for delivery fee response.
    """
    fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    available = serializers.BooleanField()
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