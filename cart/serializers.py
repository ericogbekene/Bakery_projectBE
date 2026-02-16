from rest_framework import serializers
from django.conf import settings
from cart.models import Cart, CartItem, DeliveryInfo
from products.models import Product
from decimal import Decimal


class CartItemProductSerializer(serializers.ModelSerializer):
    """
    Simplified product serializer for cart items.
    """
    image_url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'image_url', 'thumbnail_url', 'price']


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual cart items.
    """
    product = CartItemProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    customization_summary = serializers.CharField(source='get_customization_summary', read_only=True)
    price_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity',
            'flavour_1', 'flavour_2', 'size', 'colours',
            'cake_topper', 'candle', 'birthday_card', 
            'chocolate', 'wine', 'whiskey_200ml',
            'additional_notes',
            'base_price', 'customization_cost',
            'unit_price', 'total_price',
            'customization_summary', 'price_breakdown',
            'added_at'
        ]
        read_only_fields = ['id', 'base_price', 'customization_cost', 
                           'unit_price', 'total_price', 'added_at']
    
    def get_price_breakdown(self, obj):
        """
        Get detailed price breakdown for the item.
        """
        return {
            'design_price': str(obj.base_price),
            'size_multiplier': str(obj.size_multiplier_value),
            'flavor_multiplier': str(obj.flavor_multiplier_value),
            'customizations': obj.get_addons_breakdown(),
            'unit_price': str(obj.unit_price),
            'quantity': obj.quantity,
            'total': str(obj.total_item_price)
        }
    
    def validate(self, data):
        """
        Validate cart item data.
        """
        product = data.get('product')
        
        # Only validate cakes
        if product and product.is_cake:
            # Size is required for cakes
            if not data.get('size'):
                raise serializers.ValidationError({
                    'size': 'Size is required for cakes.'
                })
            
            # At least one flavor required for cakes
            if not data.get('flavour_1'):
                raise serializers.ValidationError({
                    'flavour_1': 'At least one flavor is required for cakes.'
                })
        
        return data


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    # Cake customization fields
    flavour_1 = serializers.CharField(required=False, allow_blank=True)
    flavour_2 = serializers.CharField(required=False, allow_blank=True)
    size = serializers.CharField(required=False, allow_blank=True)
    colours = serializers.CharField(required=False, allow_blank=True)
    
    # Add-ons
    cake_topper = serializers.IntegerField(min_value=0, default=0)
    candle = serializers.IntegerField(min_value=0, default=0)
    birthday_card = serializers.IntegerField(min_value=0, default=0)
    chocolate = serializers.IntegerField(min_value=0, default=0)
    wine = serializers.IntegerField(min_value=0, default=0)
    whiskey_200ml = serializers.IntegerField(min_value=0, default=0)
    
    additional_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """
        Validate the product exists and is available.
        """
        try:
            product = Product.objects.get(id=data['product_id'], available=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({
                'product_id': 'Product not found or not available.'
            })
        
        # Validate cake requirements
        if product.is_cake:
            if not data.get('size'):
                raise serializers.ValidationError({
                    'size': 'Size is required for cakes.'
                })
            
            if not data.get('flavour_1'):
                raise serializers.ValidationError({
                    'flavour_1': 'At least one flavor is required for cakes.'
                })
        
        # Store product in context for the view
        self.context['product'] = product
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer for updating cart item quantity.
    """
    quantity = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(
        choices=['set', 'increase', 'decrease'],
        default='set'
    )


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for the entire cart.
    """
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    delivery_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    grand_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'session_key', 'is_active',
            'items', 'item_count', 'subtotal', 
            'delivery_cost', 'grand_total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'session_key', 'created_at', 'updated_at']


class PriceCalculationSerializer(serializers.Serializer):
    """
    Serializer for real-time price calculation.
    """
    product_id = serializers.IntegerField()
    size = serializers.CharField(required=False, allow_blank=True)
    flavour_1 = serializers.CharField(required=False, allow_blank=True)
    flavour_2 = serializers.CharField(required=False, allow_blank=True)
    
    # Add-ons
    cake_topper = serializers.IntegerField(min_value=0, default=0)
    candle = serializers.IntegerField(min_value=0, default=0)
    birthday_card = serializers.IntegerField(min_value=0, default=0)
    chocolate = serializers.IntegerField(min_value=0, default=0)
    wine = serializers.IntegerField(min_value=0, default=0)
    whiskey_200ml = serializers.IntegerField(min_value=0, default=0)
    
    def validate(self, data):
        """
        Validate the product exists.
        """
        try:
            product = Product.objects.get(id=data['product_id'], available=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({
                'product_id': 'Product not found or not available.'
            })
        
        self.context['product'] = product
        return data


class DeliveryInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery information.
    """
    class Meta:
        model = DeliveryInfo
        fields = [
            'id', 'full_name', 'email', 'phone',
            'address', 'city', 'state', 'postal_code',
            'delivery_date', 'delivery_time_slot',
            'calculated_fee', 'special_instructions'
        ]
        read_only_fields = ['id', 'calculated_fee']


class GuestCartMergeSerializer(serializers.Serializer):
    """
    Serializer for merging guest cart on login.
    """
    session_key = serializers.CharField()