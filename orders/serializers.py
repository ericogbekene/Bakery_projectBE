# from rest_framework import serializers
# from decimal import Decimal
# from .models import (
#     Cart, CartItem, Order, OrderItem, OrderHistory, OrderPayment,
#     CakeCustomizationOption, CakeSizePrice, CakeFlavorPrice
# )


# # ============================================================================
# # PRICING & CUSTOMIZATION SERIALIZERS
# # ============================================================================

# class CakeCustomizationOptionSerializer(serializers.ModelSerializer):
#     """Serializer for cake customization options (toppers, candles, wine, etc.)"""
    
#     class Meta:
#         model = CakeCustomizationOption
#         fields = [
#             'id', 'customization_type', 'price_per_unit', 'description', 'is_active'
#         ]


# class CakeSizePriceSerializer(serializers.ModelSerializer):
#     """Serializer for cake size pricing"""
    
#     size_display = serializers.CharField(source='get_size_display', read_only=True)
    
#     class Meta:
#         model = CakeSizePrice
#         fields = ['id', 'size', 'size_display', 'base_price']


# class CakeFlavorPriceSerializer(serializers.ModelSerializer):
#     """Serializer for cake flavor price multipliers"""
    
#     price_increase = serializers.SerializerMethodField()
    
#     class Meta:
#         model = CakeFlavorPrice
#         fields = ['id', 'flavor', 'price_multiplier', 'price_increase']
    
#     def get_price_increase(self, obj):
#         """Calculate percentage increase from multiplier"""
#         percentage = (obj.price_multiplier - Decimal('1.00')) * 100
#         return float(percentage)


# class PricingInfoSerializer(serializers.Serializer):
#     """Serializer for pricing information"""
    
#     customizations = CakeCustomizationOptionSerializer(many=True)
#     sizes = CakeSizePriceSerializer(many=True)
#     flavors = CakeFlavorPriceSerializer(many=True)


# # ============================================================================
# # CART SERIALIZERS
# # ============================================================================

# class CartItemDetailSerializer(serializers.ModelSerializer):
#     """Detailed serializer for cart items"""
    
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     total_item_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     customization_breakdown = serializers.SerializerMethodField()
#     customization_summary = serializers.SerializerMethodField()
    
#     class Meta:
#         model = CartItem
#         fields = [
#             'id', 'product', 'product_name', 'quantity',
#             'flavour_1', 'flavour_2', 'size', 'colours',
#             'cake_topper', 'candle', 'birthday_card', 'chocolate', 'wine', 'whiskey_200ml',
#             'base_price', 'customization_cost', 'unit_price', 'total_item_price',
#             'customization_breakdown', 'customization_summary', 'additional_notes',
#             'added_at'
#         ]
    
#     def get_customization_breakdown(self, obj):
#         """Get detailed breakdown of customizations"""
#         return obj.get_customization_breakdown()
    
#     def get_customization_summary(self, obj):
#         """Get summary of customizations"""
#         return obj.get_customization_summary()


# class CartItemCreateUpdateSerializer(serializers.ModelSerializer):
#     """Serializer for creating/updating cart items"""
    
#     class Meta:
#         model = CartItem
#         fields = [
#             'product', 'quantity',
#             'flavour_1', 'flavour_2', 'size', 'colours',
#             'cake_topper', 'candle', 'birthday_card', 'chocolate', 'wine', 'whiskey_200ml',
#             'additional_notes'
#         ]
    
#     def validate_quantity(self, value):
#         """Validate quantity is positive"""
#         if value < 1:
#             raise serializers.ValidationError("Quantity must be at least 1")
#         if value > 100:
#             raise serializers.ValidationError("Quantity cannot exceed 100")
#         return value
    
#     def validate_additional_notes(self, value):
#         """Validate additional notes length"""
#         if len(value) > 1000:
#             raise serializers.ValidationError("Additional notes cannot exceed 1000 characters")
#         return value
    
#     def create(self, validated_data):
#         """Create cart item with automatic price calculation"""
#         cart_item = CartItem.objects.create(**validated_data)
#         return cart_item
    
#     def update(self, instance, validated_data):
#         """Update cart item"""
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         return instance


# class CartSummarySerializer(serializers.ModelSerializer):
#     """Serializer for cart summary with all items"""
    
#     items = CartItemDetailSerializer(many=True, read_only=True)
#     total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     item_count = serializers.IntegerField(read_only=True)
    
#     class Meta:
#         model = Cart
#         fields = ['id', 'items', 'total_price', 'item_count', 'is_active', 'created_at']


# # ============================================================================
# # ORDER ITEM SERIALIZERS
# # ============================================================================

# class OrderItemDetailSerializer(serializers.ModelSerializer):
#     """Detailed serializer for order items"""
    
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     customization_summary = serializers.SerializerMethodField()
#     addons_summary = serializers.SerializerMethodField()
    
#     class Meta:
#         model = OrderItem
#         fields = [
#             'id', 'product', 'product_name', 'quantity',
#             'flavour_1', 'flavour_2', 'size', 'colours',
#             'cake_topper', 'candle', 'birthday_card', 'chocolate', 'wine', 'whiskey_200ml',
#             'base_price', 'customization_cost', 'unit_price', 'item_total',
#             'customization_summary', 'addons_summary', 'additional_notes',
#             'created_at'
#         ]
    
#     def get_customization_summary(self, obj):
#         """Get customization summary"""
#         return obj.get_customization_summary()
    
#     def get_addons_summary(self, obj):
#         """Get add-ons summary"""
#         return obj.get_addons_summary()


# class OrderItemCreateSerializer(serializers.ModelSerializer):
#     """Serializer for creating order items"""
    
#     class Meta:
#         model = OrderItem
#         fields = [
#             'product', 'quantity',
#             'flavour_1', 'flavour_2', 'size', 'colours',
#             'cake_topper', 'candle', 'birthday_card', 'chocolate', 'wine', 'whiskey_200ml',
#             'base_price', 'customization_cost', 'unit_price',
#             'additional_notes'
#         ]


# # ============================================================================
# # ORDER HISTORY SERIALIZER
# # ============================================================================

# class OrderHistorySerializer(serializers.ModelSerializer):
#     """Serializer for order history/timeline"""
    
#     action_display = serializers.CharField(source='get_action_display', read_only=True)
#     changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
#     class Meta:
#         model = OrderHistory
#         fields = [
#             'id', 'action', 'action_display', 'description',
#             'changed_by', 'changed_by_username',
#             'timestamp', 'old_value', 'new_value'
#         ]


# # ============================================================================
# # ORDER PAYMENT SERIALIZER
# # ============================================================================

# class OrderPaymentSerializer(serializers.ModelSerializer):
#     """Serializer for order payments"""
    
#     payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
    
#     class Meta:
#         model = OrderPayment
#         fields = [
#             'id', 'amount', 'payment_method', 'payment_method_display',
#             'transaction_id', 'status', 'status_display',
#             'reference_number', 'notes',
#             'created_at', 'updated_at', 'processed_at'
#         ]


# # ============================================================================
# # ORDER SERIALIZERS
# # ============================================================================

# class OrderCreateSerializer(serializers.ModelSerializer):
#     """Serializer for creating orders"""
    
#     class Meta:
#         model = Order
#         fields = [
#             'delivery_address', 'delivery_city', 'delivery_phone',
#             'delivery_date', 'delivery_time', 'special_instructions',
#             'guest_email', 'guest_phone',
#             'discount_code'
#         ]
    
#     def validate_delivery_date(self, value):
#         """Validate delivery date is in future"""
#         from django.utils import timezone
#         if value < timezone.now().date():
#             raise serializers.ValidationError("Delivery date must be in the future")
#         return value
    
#     def validate_delivery_phone(self, value):
#         """Validate phone number format"""
#         if len(value) < 10:
#             raise serializers.ValidationError("Phone number must be at least 10 digits")
#         return value


# class OrderListSerializer(serializers.ModelSerializer):
#     """Serializer for listing orders"""
    
#     customer_name = serializers.CharField(read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
#     item_count = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Order
#         fields = [
#             'id', 'order_number', 'customer_name',
#             'status', 'status_display',
#             'payment_status', 'payment_status_display',
#             'total_amount', 'delivery_date',
#             'created_at', 'item_count'
#         ]
    
#     def get_item_count(self, obj):
#         """Get number of items in order"""
#         return obj.items.count()


# class OrderDetailSerializer(serializers.ModelSerializer):
#     """Detailed serializer for order information"""
    
#     customer_name = serializers.CharField(read_only=True)
#     customer_email = serializers.CharField(read_only=True)
#     customer_phone = serializers.CharField(read_only=True)
    
#     items = OrderItemDetailSerializer(many=True, read_only=True)
#     payments = OrderPaymentSerializer(many=True, read_only=True)
#     history = OrderHistorySerializer(many=True, read_only=True)
    
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
#     payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
#     class Meta:
#         model = Order
#         fields = [
#             'id', 'order_number',
#             'customer_name', 'customer_email', 'customer_phone',
#             'user',
#             'status', 'status_display',
#             'payment_status', 'payment_status_display',
#             'payment_method', 'payment_method_display',
#             'payment_transaction_id', 'payment_date',
#             'delivery_address', 'delivery_city', 'delivery_phone',
#             'delivery_date', 'delivery_time',
#             'special_instructions',
#             'subtotal', 'tax_amount', 'delivery_fee',
#             'discount_amount', 'discount_code',
#             'total_amount',
#             'items', 'payments', 'history',
#             'created_at', 'updated_at',
#             'confirmed_at', 'completed_at', 'cancelled_at',
#             'cancellation_reason', 'admin_notes'
#         ]
    
#     def to_representation(self, instance):
#         """Customize representation"""
#         ret = super().to_representation(instance)
        
#         # Format prices
#         for field in ['subtotal', 'tax_amount', 'delivery_fee', 'discount_amount', 'total_amount']:
#             if ret.get(field):
#                 ret[field] = f"₦{Decimal(ret[field]):,.2f}"
        
#         return ret


# class OrderStatusUpdateSerializer(serializers.ModelSerializer):
#     """Serializer for updating order status"""
    
#     class Meta:
#         model = Order
#         fields = ['status', 'admin_notes']
    
#     def validate_status(self, value):
#         """Validate status is valid"""
#         valid_statuses = ['pending', 'confirmed', 'processing', 'ready', 'completed', 'cancelled']
#         if value not in valid_statuses:
#             raise serializers.ValidationError(
#                 f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
#             )
#         return value


# class OrderCancelSerializer(serializers.ModelSerializer):
#     """Serializer for cancelling order"""
    
#     class Meta:
#         model = Order
#         fields = ['cancellation_reason']
    
#     def validate_cancellation_reason(self, value):
#         """Validate cancellation reason"""
#         if len(value) > 500:
#             raise serializers.ValidationError("Reason must be less than 500 characters")
#         return value


# class OrderPaymentInitSerializer(serializers.Serializer):
#     """Serializer for initiating payment"""
    
#     payment_method = serializers.ChoiceField(
#         choices=['credit_card', 'debit_card', 'bank_transfer', 'paypal', 'stripe', 'cash'],
#         required=True
#     )
#     payment_token = serializers.CharField(required=False, allow_blank=True)
#     reference_number = serializers.CharField(required=False, allow_blank=True)
    
#     def validate(self, data):
#         """Validate payment data"""
#         payment_method = data.get('payment_method')
#         payment_token = data.get('payment_token')
        
#         # Require token for online payments
#         if payment_method in ['credit_card', 'debit_card', 'paypal', 'stripe']:
#             if not payment_token:
#                 raise serializers.ValidationError(
#                     f"payment_token is required for {payment_method}"
#                 )
        
#         return data


# # ============================================================================
# # CHECKOUT SERIALIZERS
# # ============================================================================

# class CheckoutSummarySerializer(serializers.Serializer):
#     """Serializer for checkout summary"""
    
#     subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
#     tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
#     tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
#     delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
#     discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
#     estimated_total = serializers.DecimalField(max_digits=10, decimal_places=2)
#     item_count = serializers.IntegerField()
    
#     class Meta:
#         fields = [
#             'subtotal', 'tax_amount', 'tax_rate',
#             'delivery_fee', 'discount_amount', 'estimated_total',
#             'item_count'
#         ]


# # ============================================================================
# # COMBINED SERIALIZERS
# # ============================================================================

# class CartWithPricingSerializer(serializers.ModelSerializer):
#     """Serializer for cart with pricing information"""
    
#     items = CartItemDetailSerializer(many=True, read_only=True)
#     total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     item_count = serializers.IntegerField(read_only=True)
    
#     # Pricing info
#     tax_rate = serializers.SerializerMethodField()
#     tax_amount = serializers.SerializerMethodField()
#     delivery_fee = serializers.SerializerMethodField()
#     estimated_total = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Cart
#         fields = [
#             'id', 'items', 'total_price', 'item_count',
#             'tax_rate', 'tax_amount', 'delivery_fee', 'estimated_total',
#             'created_at'
#         ]
    
#     def get_tax_rate(self, obj):
#         """Get tax rate"""
#         return 0.10  # 10%
    
#     def get_tax_amount(self, obj):
#         """Calculate tax amount"""
#         return (obj.total_price * Decimal('0.10')).quantize(Decimal('0.01'))
    
#     def get_delivery_fee(self, obj):
#         """Get delivery fee"""
#         return Decimal('1000.00')
    
#     def get_estimated_total(self, obj):
#         """Calculate estimated total"""
#         tax = (obj.total_price * Decimal('0.10')).quantize(Decimal('0.01'))
#         delivery = Decimal('1000.00')
#         return obj.total_price + tax + delivery


# class OrderWithItemsSerializer(serializers.ModelSerializer):
#     """Serializer for order with all related data"""
    
#     customer_name = serializers.CharField(read_only=True)
#     items = OrderItemDetailSerializer(many=True, read_only=True)
#     payments = OrderPaymentSerializer(many=True, read_only=True)
#     history = OrderHistorySerializer(many=True, read_only=True)
    
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
#     class Meta:
#         model = Order
#         fields = [
#             'order_number', 'customer_name',
#             'status', 'status_display',
#             'payment_status', 'payment_status_display',
#             'items', 'payments', 'history',
#             'total_amount',
#             'delivery_address', 'delivery_date',
#             'created_at'
#         ]