from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from orders.models import (
    Order, OrderItem, OrderDelivery, OrderPickup, OrderHistory, OrderPayment,
    ORDER_STATUS_CHOICES, PAYMENT_STATUS_CHOICES
)
from products.models import Product
from cart.models import Cart
from decimal import Decimal


class OrderItemProductSerializer(serializers.ModelSerializer):
    """
    Simplified product serializer for order items.
    """
    image_url = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'image_url']


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items (read-only).
    """
    product = OrderItemProductSerializer(read_only=True)
    customization_summary = serializers.SerializerMethodField()
    addons_summary = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity',
            'flavour_1', 'flavour_2', 'size', 'colours',
            'cake_topper', 'candle', 'birthday_card',
            'chocolate', 'wine', 'whiskey_200ml',
            'additional_notes',
            'base_price', 'customization_cost', 'unit_price', 'item_total',
            'customization_summary', 'addons_summary',
            'created_at'
        ]
        read_only_fields = [
            'id', 'product', 'quantity',
            'flavour_1', 'flavour_2', 'size', 'colours',
            'cake_topper', 'candle', 'birthday_card',
            'chocolate', 'wine', 'whiskey_200ml',
            'additional_notes',
            'base_price', 'customization_cost', 'unit_price', 'item_total',
            'customization_summary', 'addons_summary',
            'created_at'
        ]

    def get_customization_summary(self, obj):
        """Get human-readable customization summary."""
        return obj.get_customization_summary()

    def get_addons_summary(self, obj):
        """Get human-readable add-ons summary."""
        return obj.get_addons_summary()


class OrderDeliverySerializer(serializers.ModelSerializer):
    """
    Serializer for order delivery information.
    """
    delivery_time_slot = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )
    special_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )

    class Meta:
        model = OrderDelivery
        fields = [
            'id', 'address', 'city', 'state', 'postal_code',
            'delivery_date', 'delivery_time_slot',
            'delivery_zone', 'delivery_fee',
            'special_instructions', 'is_delivered', 'delivered_at'
        ]
        read_only_fields = ['id', 'is_delivered', 'delivered_at']


class OrderPickupSerializer(serializers.ModelSerializer):
    """
    Serializer for order pickup information.
    """
    pickup_time_slot = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )
    special_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )

    class Meta:
        model = OrderPickup
        fields = [
            'id', 'pickup_date', 'pickup_time_slot',
            'special_instructions', 'is_picked_up', 'picked_up_at'
        ]
        read_only_fields = ['id', 'is_picked_up', 'picked_up_at']


class OrderHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for order history/audit trail.
    """
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True, default='System')

    class Meta:
        model = OrderHistory
        fields = [
            'id', 'action', 'action_display', 'description',
            'changed_by', 'changed_by_username', 'timestamp',
            'old_value', 'new_value'
        ]
        read_only_fields = [
            'id', 'action', 'action_display', 'description',
            'changed_by', 'changed_by_username', 'timestamp',
            'old_value', 'new_value'
        ]


class OrderPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for order payments.
    """
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderPayment
        fields = [
            'id', 'amount', 'payment_method', 'payment_method_display',
            'transaction_id', 'status', 'status_display',
            'reference_number', 'notes', 'processed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']


class OrderListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for order list views.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()
    fulfillment_summary = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'fulfillment_type', 'fulfillment_summary',
            'total_amount', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'item_count',
            'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'fulfillment_type', 'fulfillment_summary',
            'total_amount', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'item_count',
            'created_at', 'completed_at'
        ]

    def get_item_count(self, obj):
        """Get total number of items in order."""
        return obj.items.count()

    def get_fulfillment_summary(self, obj):
        """Return address/date for delivery, or pickup date for pickup — whichever applies."""
        if obj.fulfillment_type == 'delivery' and hasattr(obj, 'delivery'):
            return {
                'address': obj.delivery.address,
                'date': obj.delivery.delivery_date,
            }
        if obj.fulfillment_type == 'pickup' and hasattr(obj, 'pickup'):
            return {
                'date': obj.pickup.pickup_date,
            }
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single order view.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    delivery = OrderDeliverySerializer(read_only=True)
    pickup = OrderPickupSerializer(read_only=True)
    history = OrderHistorySerializer(many=True, read_only=True)
    payments = OrderPaymentSerializer(many=True, read_only=True)
    customer_type = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number',
            'customer_name', 'customer_email', 'customer_phone',
            'customer_type', 'user', 'fulfillment_type',
            'subtotal', 'delivery_fee', 'total_amount',
            'status', 'status_display',
            'payment_status', 'payment_status_display',
            'payment_method_display',
            'paystack_transaction_id',
            'paystack_reference',
            'payment_date',
            'items', 'delivery', 'pickup', 'history', 'payments',
            'created_at', 'confirmed_at', 'processing_at',
            'ready_at', 'completed_at', 'cancelled_at',
            'cancellation_reason', 'admin_notes'
        ]
        read_only_fields = [
            'id', 'order_number',
            'customer_name', 'customer_email', 'customer_phone',
            'customer_type', 'user', 'fulfillment_type',
            'subtotal', 'delivery_fee', 'total_amount',
            'status', 'status_display',
            'payment_status', 'payment_status_display',
            'payment_method_display',
            'paystack_transaction_id',
            'paystack_reference',
            'payment_date',
            'items', 'delivery', 'pickup', 'history', 'payments',
            'created_at', 'confirmed_at', 'processing_at',
            'ready_at', 'completed_at', 'cancelled_at',
            'cancellation_reason', 'admin_notes'
        ]

    def get_payment_method_display(self, obj):
        """Always return Paystack as the payment method."""
        return "Paystack"

    def get_customer_type(self, obj):
        """Determine if customer is registered or guest."""
        if obj.user:
            return 'registered'
        return 'guest'


class CreateOrderSerializer(serializers.Serializer):
    """
    Serializer for creating an order from cart.
    Payment method is fixed as Paystack.

    Delivery fields are required only when the cart's fulfillment_type is
    'delivery'. Pickup fields are required only when it's 'pickup'.
    """
    # Customer information
    customer_name = serializers.CharField(max_length=100)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20)

    # Delivery information (required only for delivery orders)
    delivery_address = serializers.CharField(required=False, allow_blank=True, default="")
    delivery_city = serializers.CharField(required=False, allow_blank=True, default="")
    delivery_state = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    delivery_postal_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    delivery_date = serializers.DateField(required=False, allow_null=True, default=None)
    delivery_time_slot = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )

    # Pickup information (required only for pickup orders)
    pickup_date = serializers.DateField(required=False, allow_null=True, default=None)
    pickup_time_slot = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )

    special_instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=""
    )

    paystack_reference = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")

    def validate(self, data):
        """Validate order can be created - WITHOUT session access."""
        request = self.context.get('request')

        # Try to get cart WITHOUT accessing session
        cart = None

        if 'cart' in self.context:
            cart = self.context['cart']

        if not cart and request:
            try:
                if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                    cart = Cart.objects.filter(user=request.user, is_active=True).first()
            except Exception:
                pass

            if not cart and hasattr(request, 'session'):
                try:
                    cart_id = request.session.get('cart_id')
                    if cart_id:
                        cart = Cart.objects.filter(id=cart_id, is_active=True).first()
                except Exception:
                    pass

        if not cart:
            raise serializers.ValidationError({"cart": "No active cart found. Please add items to your cart."})

        if cart.items.count() == 0:
            raise serializers.ValidationError({"cart": "Cart is empty. Please add items before ordering."})

        # ── Conditional validation based on fulfillment type ──────────
        if cart.fulfillment_type == 'delivery':
            missing = {}
            if not data.get('delivery_address'):
                missing['delivery_address'] = "This field is required for delivery orders."
            if not data.get('delivery_city'):
                missing['delivery_city'] = "This field is required for delivery orders."
            if not data.get('delivery_date'):
                missing['delivery_date'] = "This field is required for delivery orders."
            if missing:
                raise serializers.ValidationError(missing)

            if data.get('delivery_date') and data['delivery_date'] < timezone.now().date():
                raise serializers.ValidationError(
                    {"delivery_date": "Delivery date cannot be in the past."}
                )

        else:  # pickup
            if not data.get('pickup_date'):
                raise serializers.ValidationError(
                    {"pickup_date": "This field is required for pickup orders."}
                )
            if data['pickup_date'] < timezone.now().date():
                raise serializers.ValidationError(
                    {"pickup_date": "Pickup date cannot be in the past."}
                )

        # Store cart in context for the view
        self.context['cart'] = cart
        return data


class OrderCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling an order.
    """
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating order status (admin only).
    """
    status = serializers.ChoiceField(choices=ORDER_STATUS_CHOICES)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    notify_customer = serializers.BooleanField(default=True)


class OrderPaymentUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating payment status (admin only).
    """
    payment_status = serializers.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    paystack_reference = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)