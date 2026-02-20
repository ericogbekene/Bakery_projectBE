# Order Models Implementation Guide

## Overview

The Order system consists of 4 interconnected models:
1. **Order** - Main order record
2. **OrderItem** - Individual items in the order
3. **OrderHistory** - Audit trail of status changes
4. **OrderPayment** - Payment transaction records

---

## Model Details

### 1. Order Model

The main order record that tracks customer orders from creation to completion.

**Key Fields:**

#### Order Identification
- `order_number` - Unique order ID (auto-generated: ORD-20240129-ABC12345)
- `user` - Link to User (null for guest orders)
- `guest_email` - Email for guest checkout
- `guest_phone` - Phone for guest checkout
- `cart` - Reference to original cart

#### Delivery Information
- `delivery_address` - Full delivery address
- `delivery_city` - City/Area
- `delivery_phone` - Contact phone for delivery
- `delivery_date` - Requested delivery date
- `delivery_time` - Preferred delivery time (optional)
- `special_instructions` - Notes for baker/delivery

#### Pricing
- `subtotal` - Total before taxes/fees (₦47,500.00)
- `tax_amount` - Tax calculation (₦4,750.00)
- `delivery_fee` - Shipping cost (₦1,000.00)
- `discount_amount` - Discount applied (₦0.00)
- `discount_code` - Coupon code used
- `total_amount` - Final total (₦53,250.00)

#### Status Tracking
- `status` - Order status (pending, confirmed, processing, ready, completed, cancelled)
- `payment_status` - Payment status (pending, paid, failed, refunded)
- `payment_method` - How to pay (credit_card, debit_card, bank_transfer, paypal, stripe, cash)
- `payment_transaction_id` - Payment gateway ID
- `payment_date` - When payment received

#### Timestamps
- `created_at` - When order was created
- `updated_at` - Last update
- `confirmed_at` - When confirmed
- `completed_at` - When completed
- `cancelled_at` - When cancelled
- `cancellation_reason` - Why cancelled

#### Notes
- `admin_notes` - Internal staff notes

**Status Flow:**
```
pending → confirmed → processing → ready → completed
          ↓
        cancelled
```

**Properties:**
```python
order.is_pending        # Check if pending
order.is_confirmed      # Check if confirmed
order.is_processing     # Check if processing
order.is_ready          # Check if ready
order.is_completed      # Check if completed
order.is_cancelled      # Check if cancelled
order.is_paid           # Check if payment received
order.customer_name     # Get customer name
order.customer_email    # Get customer email
order.customer_phone    # Get customer phone
```

---

### 2. OrderItem Model

Individual items within an order. Snapshot of CartItem at order time.

**Key Fields:**

#### Basic Info
- `order` - Parent order (ForeignKey)
- `product` - Product ordered
- `quantity` - Number of cakes (1, 2, 3, etc.)

#### Customization Details (Snapshot)
- `flavour_1` - First flavor (Vanilla, Chocolate, etc.)
- `flavour_2` - Second flavor (optional)
- `size` - Cake size (6", 8", 10", 12", 14")
- `colours` - Colors/decorations

#### Add-ons (Snapshot)
- `cake_topper` - Number of toppers
- `candle` - Number of candles
- `birthday_card` - Number of cards
- `chocolate` - Number of chocolate boxes
- `wine` - Number of wine bottles
- `whiskey_200ml` - Number of whiskey bottles

#### Pricing (Frozen at order time)
- `base_price` - Base price per cake (₦32,500.00)
- `customization_cost` - Cost of add-ons per cake (₦15,000.00)
- `unit_price` - Price per cake (₦47,500.00)
- `item_total` - Total for line (₦47,500.00)

#### Notes
- `additional_notes` - Special instructions for this item
- `created_at` - When added to order

**Methods:**
```python
item.total_price                    # Get item total
item.get_customization_summary()   # "Flavour 1: Marble, Size: 12""
item.get_addons_summary()          # "2 topper(s), 4 candle(s), 1 wine"
```

---

### 3. OrderHistory Model

Audit trail tracking all changes to an order.

**Key Fields:**
- `order` - Parent order
- `action` - What happened (created, confirmed, payment_received, processing, ready, delivered, completed, cancelled, refunded, status_changed)
- `description` - Details about the action
- `changed_by` - Staff member who made the change
- `timestamp` - When it happened
- `old_value` - Previous value (for changes)
- `new_value` - New value (for changes)

**Example Timeline:**
```
2024-01-29 10:00 - Order Created (by Customer)
2024-01-29 10:30 - Order Confirmed (by Admin)
2024-01-29 11:00 - Payment Received (by System)
2024-01-29 14:00 - Processing Started (by Baker)
2024-01-29 17:00 - Ready for Pickup (by Baker)
2024-01-29 18:00 - Order Completed (by Customer)
```

---

### 4. OrderPayment Model

Track payment transactions separately from Order.

**Key Fields:**
- `order` - Parent order
- `amount` - Payment amount (₦53,250.00)
- `payment_method` - Method used (credit_card, bank_transfer, etc.)
- `transaction_id` - Payment gateway transaction ID (unique)
- `status` - Payment status (pending, paid, failed, refunded)
- `reference_number` - Bank reference for verification
- `notes` - Payment notes
- `created_at` - When initiated
- `updated_at` - Last update
- `processed_at` - When completed

**Why Separate:**
- Multiple payment attempts
- Partial payments
- Payment reconciliation
- Payment audit trail
- Refund tracking

---

## Database Relationships

```
User
  ↓
Order (user_id)
  ├─ OrderItem (order_id) [Multiple]
  ├─ OrderHistory (order_id) [Multiple]
  └─ OrderPayment (order_id) [Multiple]
```

---

## Status Workflow

### Order Status
```
PENDING
  ↓
CONFIRMED (customer confirms)
  ↓
PROCESSING (baker starts)
  ↓
READY (cake ready for pickup/delivery)
  ↓
COMPLETED (delivered/picked up)
```

### Payment Status
```
PENDING
  ↓
PAID (payment received)
```

### Combined Example
```
Order Created: status=pending, payment_status=pending
Customer Pays: status=pending, payment_status=paid
Baker Confirms: status=confirmed, payment_status=paid
Baker Starts: status=processing, payment_status=paid
Cake Ready: status=ready, payment_status=paid
Order Delivered: status=completed, payment_status=paid
```

---

## Implementation Steps

### Step 1: Add to models.py

Copy the order model code to the end of your `models.py` file:

```python
# At the end of cart/models.py

# ============================================================================
# ORDER MODELS
# ============================================================================

# Paste all Order, OrderItem, OrderHistory, and OrderPayment models here
```

### Step 2: Create Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Register in admin.py

Add to your `admin.py`:

```python
from .models import Order, OrderItem, OrderHistory, OrderPayment

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__username', 'guest_email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'item_total']
    list_filter = ['created_at']
    readonly_fields = ['order', 'unit_price', 'item_total', 'created_at']

@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'action', 'changed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['order', 'timestamp']

@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
```

---

## Example Usage

### Create an Order from Cart

```python
from decimal import Decimal
from .models import Order, OrderItem

# Create order from cart
cart = Cart.objects.get(id=1)

order = Order.objects.create(
    user=request.user,
    cart=cart,
    delivery_address="123 Main St, Apartment 4B",
    delivery_city="Abuja",
    delivery_phone="+234 701 234 5678",
    delivery_date="2024-02-15",
    special_instructions="Please ring doorbell twice",
    subtotal=Decimal('47500.00'),
    tax_amount=Decimal('4750.00'),
    delivery_fee=Decimal('1000.00'),
    total_amount=Decimal('53250.00'),
    payment_method='stripe'
)

# Add items from cart
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
        unit_price=cart_item.unit_price
    )

# Clear cart after order
cart.is_active = False
cart.save()

return order
```

### Confirm Order

```python
from django.utils.timezone import now

order = Order.objects.get(order_number='ORD-20240129-ABC12345')

# Confirm order
order.status = 'confirmed'
order.confirmed_at = now()
order.save()

# Add history entry
OrderHistory.objects.create(
    order=order,
    action='confirmed',
    description='Order confirmed by admin',
    changed_by=request.user,
    old_value='pending',
    new_value='confirmed'
)
```

### Record Payment

```python
payment = OrderPayment.objects.create(
    order=order,
    amount=order.total_amount,
    payment_method='stripe',
    transaction_id='ch_1234567890',
    status='paid',
    reference_number='REF-2024-001'
)

# Update order
order.payment_status = 'paid'
order.payment_date = now()
order.save()

# Add history
OrderHistory.objects.create(
    order=order,
    action='payment_received',
    description=f'Payment received via {payment.payment_method}',
    old_value='pending',
    new_value='paid'
)
```

### Get Order Details

```python
order = Order.objects.get(order_number='ORD-20240129-ABC12345')

# Customer info
print(order.customer_name)
print(order.customer_email)
print(order.customer_phone)

# Items
for item in order.items.all():
    print(f"{item.quantity}x {item.product.name}")
    print(item.get_customization_summary())
    print(item.get_addons_summary())
    print(f"Total: ₦{item.item_total:,.2f}")

# Timeline
for history in order.history.all():
    print(f"{history.timestamp} - {history.get_action_display()}")

# Payments
for payment in order.payments.all():
    print(f"₦{payment.amount} via {payment.payment_method}")
```

---

## API Endpoints (Future)

You'll want to create API endpoints for:

```
GET    /api/orders/                    # List customer's orders
POST   /api/orders/                    # Create order from cart
GET    /api/orders/{order_number}/     # Get order details
PUT    /api/orders/{order_number}/     # Update order
GET    /api/orders/{order_number}/items/  # Get order items
GET    /api/orders/{order_number}/history/ # Get order timeline
POST   /api/orders/{order_number}/pay/    # Process payment
```

---

## Admin Interface Features

Once registered in admin:

1. **View Orders**
   - Filter by status, payment status, date
   - Search by order number, customer name, email
   - See all customer details
   - See items inline

2. **Manage Order Status**
   - Change status
   - Add notes
   - View status history

3. **Payment Tracking**
   - See payment status
   - Track transactions
   - Handle refunds

4. **Order History**
   - Audit trail
   - See who made changes
   - Timestamps for all actions

---

## Indexing & Performance

Database indexes on:
- `order_number` - Fast lookup
- `user + created_at` - Quick customer order list
- `status` - Filter by status
- `payment_status` - Filter by payment

---

## Next Steps

1. ✅ Add models to models.py
2. ✅ Run migrations
3. ✅ Register in admin.py
4. Create OrderSerializer for API
5. Create Order views for API
6. Add order creation logic (from cart)
7. Add payment integration
8. Add order notifications (email)
9. Add order tracking (customer)
10. Create invoice generation

---

## Summary

The Order system provides:
- ✅ Complete order tracking
- ✅ Payment management
- ✅ Audit trail
- ✅ Status workflow
- ✅ Customer history
- ✅ Admin control