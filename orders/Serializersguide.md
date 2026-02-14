# Serializers Guide - Complete Reference

## Overview

Serializers are responsible for converting Django model instances to/from JSON. This guide covers all serializers needed for the cake shop API.

---

## Setup

### 1. Add to cart/serializers.py

Replace your existing `serializers.py` with the content from `order_serializers.py`:

```python
# In cart/serializers.py
# Copy entire content of order_serializers.py
```

Or append to existing file:

```python
# At the end of your existing serializers.py
# Paste order-related serializers
```

### 2. Import in Views

```python
from .serializers import (
    # Pricing
    CakeCustomizationOptionSerializer,
    CakeSizePriceSerializer,
    CakeFlavorPriceSerializer,
    
    # Cart
    CartItemDetailSerializer,
    CartSummarySerializer,
    
    # Order
    OrderDetailSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    
    # And others as needed
)
```

---

## Serializer Types

### 1. Read-Only Serializers

Used for displaying data (GET requests):
- `CartItemDetailSerializer`
- `CartSummarySerializer`
- `OrderDetailSerializer`
- `OrderListSerializer`
- `OrderItemDetailSerializer`
- `OrderHistorySerializer`
- `OrderPaymentSerializer`

### 2. Write-Only Serializers

Used for creating/updating data (POST/PUT requests):
- `CartItemCreateUpdateSerializer`
- `OrderCreateSerializer`
- `OrderStatusUpdateSerializer`
- `OrderCancelSerializer`

### 3. Combined Serializers

Used for both reading and writing:
- `CakeCustomizationOptionSerializer`
- `CakeSizePriceSerializer`
- `CakeFlavorPriceSerializer`

---

## Detailed Serializers

### Pricing Serializers

#### CakeCustomizationOptionSerializer
Represents customization options (toppers, candles, wine, etc.)

**Fields:**
```python
{
    'id': 1,
    'customization_type': 'topper',
    'price_per_unit': '1500.00',
    'description': 'Gold cake topper',
    'is_active': true
}
```

#### CakeSizePriceSerializer
Represents cake size pricing

**Fields:**
```python
{
    'id': 1,
    'size': '12',
    'size_display': '12 Inches',
    'base_price': '25000.00'
}
```

#### CakeFlavorPriceSerializer
Represents flavor price multipliers

**Fields:**
```python
{
    'id': 1,
    'flavor': 'Marble',
    'price_multiplier': '1.3',
    'price_increase': 30.0  # Percentage
}
```

---

### Cart Serializers

#### CartItemDetailSerializer
Used for displaying cart items with full details

**Fields:**
```python
{
    'id': 1,
    'product': 1,
    'product_name': 'Chocolate Cake',
    'quantity': 1,
    'flavour_1': 'Marble',
    'flavour_2': 'Vanilla',
    'size': '12',
    'colours': 'pink, white',
    'cake_topper': 1,
    'candle': 4,
    'birthday_card': 0,
    'chocolate': 0,
    'wine': 1,
    'whiskey_200ml': 0,
    'base_price': '32500.00',
    'customization_cost': '15000.00',
    'unit_price': '47500.00',
    'total_item_price': '47500.00',
    'customization_breakdown': {
        'items': [...],
        'total': '15000.00'
    },
    'customization_summary': 'Flavour 1: Marble, Flavour 2: Vanilla, Size: 12',
    'additional_notes': 'Extra moist',
    'added_at': '2024-01-29T10:00:00Z'
}
```

**Use Cases:**
- Display items in cart
- Show full item details

#### CartItemCreateUpdateSerializer
Used for creating/updating cart items

**Fields (Input):**
```python
{
    'product': 1,
    'quantity': 1,
    'flavour_1': 'Marble',
    'flavour_2': 'Vanilla',
    'size': '12',
    'colours': 'pink',
    'cake_topper': 1,
    'candle': 4,
    'birthday_card': 0,
    'chocolate': 0,
    'wine': 1,
    'whiskey_200ml': 0,
    'additional_notes': 'Extra moist'
}
```

**Validation:**
- `quantity`: 1-100
- `additional_notes`: Max 1000 characters
- `product`: Required, must exist

**Use Cases:**
- Add item to cart
- Update cart item
- Modify quantities/customizations

#### CartSummarySerializer
Used for displaying full cart

**Fields:**
```python
{
    'id': 1,
    'items': [...],  # CartItemDetailSerializer
    'total_price': '47500.00',
    'item_count': 1,
    'is_active': true,
    'created_at': '2024-01-29T09:00:00Z'
}
```

**Use Cases:**
- Display cart page
- Show cart in checkout
- API response for GET /api/cart/

---

### Order Item Serializers

#### OrderItemDetailSerializer
Detailed order item information

**Fields:**
```python
{
    'id': 1,
    'product': 1,
    'product_name': 'Chocolate Cake',
    'quantity': 1,
    'flavour_1': 'Marble',
    'flavour_2': 'Vanilla',
    'size': '12',
    'cake_topper': 1,
    'candle': 4,
    'base_price': '32500.00',
    'customization_cost': '15000.00',
    'unit_price': '47500.00',
    'item_total': '47500.00',
    'customization_summary': 'Flavour 1: Marble, Size: 12',
    'addons_summary': '1 topper(s), 4 candle(s), 1 wine',
    'additional_notes': 'Extra moist',
    'created_at': '2024-01-29T10:00:00Z'
}
```

**Use Cases:**
- Display order details
- Show order items in confirmation
- Order history

---

### Order Serializers

#### OrderCreateSerializer
Used when creating orders

**Fields (Input):**
```python
{
    'delivery_address': '123 Main St, Apt 4B',
    'delivery_city': 'Abuja',
    'delivery_phone': '+234 701 234 5678',
    'delivery_date': '2024-02-15',
    'delivery_time': '14:00',
    'special_instructions': 'Ring doorbell twice',
    'guest_email': 'customer@example.com',
    'guest_phone': '+234 701 234 5678',
    'discount_code': 'SAVE10'
}
```

**Validation:**
- `delivery_date`: Must be in future
- `delivery_phone`: Min 10 digits
- All required fields checked

**Use Cases:**
- Create order from checkout
- Validate checkout data

#### OrderListSerializer
Used for listing orders

**Fields:**
```python
{
    'id': 1,
    'order_number': 'ORD-20240129-ABC12345',
    'customer_name': 'John Doe',
    'status': 'confirmed',
    'status_display': 'Confirmed',
    'payment_status': 'paid',
    'payment_status_display': 'Paid',
    'total_amount': '53250.00',
    'delivery_date': '2024-02-15',
    'created_at': '2024-01-29T10:00:00Z',
    'item_count': 1
}
```

**Use Cases:**
- List customer orders
- Display order history
- Show order summary in dashboard

#### OrderDetailSerializer
Complete order information

**Fields:**
```python
{
    'id': 1,
    'order_number': 'ORD-20240129-ABC12345',
    'customer_name': 'John Doe',
    'customer_email': 'john@example.com',
    'customer_phone': '+234 701 234 5678',
    'user': 1,
    'status': 'confirmed',
    'status_display': 'Confirmed',
    'payment_status': 'paid',
    'payment_status_display': 'Paid',
    'payment_method': 'stripe',
    'payment_method_display': 'Stripe',
    'payment_transaction_id': 'ch_1234567890',
    'payment_date': '2024-01-29T10:30:00Z',
    'delivery_address': '123 Main St, Apt 4B',
    'delivery_city': 'Abuja',
    'delivery_phone': '+234 701 234 5678',
    'delivery_date': '2024-02-15',
    'delivery_time': '14:00:00',
    'special_instructions': 'Ring doorbell twice',
    'subtotal': '₦47,500.00',
    'tax_amount': '₦4,750.00',
    'delivery_fee': '₦1,000.00',
    'discount_amount': '₦0.00',
    'discount_code': '',
    'total_amount': '₦53,250.00',
    'items': [...],  # OrderItemDetailSerializer
    'payments': [...],  # OrderPaymentSerializer
    'history': [...],  # OrderHistorySerializer
    'created_at': '2024-01-29T10:00:00Z',
    'updated_at': '2024-01-29T10:30:00Z',
    'confirmed_at': '2024-01-29T11:00:00Z',
    'completed_at': null,
    'cancelled_at': null,
    'cancellation_reason': '',
    'admin_notes': ''
}
```

**Features:**
- Includes all order details
- Shows all items with customizations
- Shows all payments
- Shows complete order history
- Auto-formats prices with ₦ symbol

**Use Cases:**
- Order confirmation page
- Order tracking
- Admin order view

---

### Order Payment & History Serializers

#### OrderPaymentSerializer
Payment transaction information

**Fields:**
```python
{
    'id': 1,
    'amount': '53250.00',
    'payment_method': 'stripe',
    'payment_method_display': 'Stripe',
    'transaction_id': 'ch_1234567890',
    'status': 'paid',
    'status_display': 'Paid',
    'reference_number': 'REF-2024-001',
    'notes': 'Payment successful',
    'created_at': '2024-01-29T10:30:00Z',
    'updated_at': '2024-01-29T10:30:00Z',
    'processed_at': '2024-01-29T10:30:00Z'
}
```

#### OrderHistorySerializer
Order status change history

**Fields:**
```python
{
    'id': 1,
    'action': 'confirmed',
    'action_display': 'Order Confirmed',
    'description': 'Order confirmed by admin',
    'changed_by': 1,
    'changed_by_username': 'admin',
    'timestamp': '2024-01-29T11:00:00Z',
    'old_value': 'pending',
    'new_value': 'confirmed'
}
```

---

## Special Features

### 1. Automatic Calculations

Some serializers automatically calculate fields:

```python
# CartWithPricingSerializer
tax_amount = total_price * 0.10
delivery_fee = 1000.00
estimated_total = subtotal + tax + delivery

# CakeFlavorPriceSerializer
price_increase = (multiplier - 1.0) * 100
```

### 2. Formatted Output

Prices automatically formatted:

```python
# OrderDetailSerializer
'total_amount': '₦53,250.00'  # Instead of '53250.00'
'subtotal': '₦47,500.00'
'tax_amount': '₦4,750.00'
```

### 3. Nested Serializers

Includes related data:

```python
# OrderDetailSerializer includes:
items: OrderItemDetailSerializer (many)
payments: OrderPaymentSerializer (many)
history: OrderHistorySerializer (many)
```

### 4. Display Fields

Shows both raw and display values:

```python
{
    'status': 'confirmed',  # Raw value
    'status_display': 'Confirmed',  # Display value
    'payment_method': 'stripe',  # Raw
    'payment_method_display': 'Stripe'  # Display
}
```

---

## Validation Examples

### Quantity Validation
```python
# CartItemCreateUpdateSerializer
def validate_quantity(self, value):
    if value < 1:
        raise ValidationError("Quantity must be at least 1")
    if value > 100:
        raise ValidationError("Quantity cannot exceed 100")
    return value
```

### Phone Validation
```python
# OrderCreateSerializer
def validate_delivery_phone(self, value):
    if len(value) < 10:
        raise ValidationError("Phone must be at least 10 digits")
    return value
```

### Date Validation
```python
# OrderCreateSerializer
def validate_delivery_date(self, value):
    from django.utils import timezone
    if value < timezone.now().date():
        raise ValidationError("Delivery date must be in the future")
    return value
```

---

## Usage Examples

### 1. Serialize Cart Items

```python
from .serializers import CartItemDetailSerializer

# Single item
serializer = CartItemDetailSerializer(cart_item)
print(serializer.data)

# Multiple items
serializer = CartItemDetailSerializer(cart.items.all(), many=True)
print(serializer.data)
```

### 2. Create Cart Item

```python
from .serializers import CartItemCreateUpdateSerializer

data = {
    'product': 1,
    'quantity': 1,
    'size': '12',
    'flavour_1': 'Marble'
}

serializer = CartItemCreateUpdateSerializer(data=data)
if serializer.is_valid():
    cart_item = serializer.save(cart=cart)
else:
    print(serializer.errors)
```

### 3. Serialize Order

```python
from .serializers import OrderDetailSerializer

serializer = OrderDetailSerializer(order)
print(serializer.data)
```

### 4. Create Order

```python
from .serializers import OrderCreateSerializer

data = {
    'delivery_address': '123 Main St',
    'delivery_city': 'Abuja',
    'delivery_phone': '+234 701 234 5678',
    'delivery_date': '2024-02-15'
}

serializer = OrderCreateSerializer(data=data)
if serializer.is_valid():
    # Use in your view
    order_data = serializer.validated_data
else:
    print(serializer.errors)
```

---

## Error Responses

### Validation Errors

```json
{
    "success": false,
    "errors": {
        "quantity": ["Quantity must be at least 1"],
        "delivery_date": ["Delivery date must be in the future"]
    }
}
```

### Field Errors

```json
{
    "success": false,
    "errors": {
        "non_field_errors": ["Invalid data"]
    }
}
```

---

## Performance Tips

### 1. Use select_related()

```python
# For ForeignKey relationships
orders = Order.objects.select_related('user').all()
serializer = OrderListSerializer(orders, many=True)
```

### 2. Use prefetch_related()

```python
# For reverse relationships
orders = Order.objects.prefetch_related('items', 'history').all()
serializer = OrderDetailSerializer(orders, many=True)
```

### 3. Limit Fields

```python
# Only include necessary fields
class OrderMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_number', 'status', 'total_amount']
```

---

## Summary

Serializers included:
- ✅ 6 Pricing serializers
- ✅ 3 Cart serializers
- ✅ 5 Order serializers
- ✅ 5 Supporting serializers

All serializers:
- Include validation
- Handle formatting
- Support nested data
- Provide error messages
- Follow REST best practices