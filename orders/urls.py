from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    
    # ========================================================================
    # PRICING & PRODUCT INFO ENDPOINTS
    # ========================================================================
    
    # Get all pricing information (sizes, flavors, customizations)
    path(
        'api/pricing/',
        views.PricingInfoAPIView.as_view(),
        name='pricing_info'
    ),
    
    # Get product details with pricing
    path(
        'api/products/<int:product_id>/details/',
        views.ProductDetailAPIView.as_view(),
        name='product_detail'
    ),
    
    # Calculate cake price based on selections
    path(
        'api/calculate-cake-price/',
        views.CalculateCakePriceAPIView.as_view(),
        name='calculate_price'
    ),
    
    
    # ========================================================================
    # CART MANAGEMENT ENDPOINTS
    # ========================================================================
    
    # Get full cart details
    path(
        'api/cart/',
        views.CartDetailAPIView.as_view(),
        name='cart_detail'
    ),
    
    # Add item to cart
    path(
        'api/cart/add/',
        views.AddToCartAPIView.as_view(),
        name='add_to_cart'
    ),
    
    # Update cart item (quantity, customizations)
    path(
        'api/cart/item/<int:cart_item_id>/',
        views.UpdateCartItemAPIView.as_view(),
        name='update_cart_item'
    ),
    
    # Remove item from cart
    path(
        'api/cart/item/<int:cart_item_id>/delete/',
        views.RemoveFromCartAPIView.as_view(),
        name='remove_from_cart'
    ),
    
    # Clear entire cart
    path(
        'api/cart/clear/',
        views.ClearCartAPIView.as_view(),
        name='clear_cart'
    ),
    
    # Get item count in cart
    path(
        'api/cart/count/',
        views.CartItemCountAPIView.as_view(),
        name='cart_count'
    ),
    
    # Get cart total price
    path(
        'api/cart/total/',
        views.CartTotalAPIView.as_view(),
        name='cart_total'
    ),
    
    
    # ========================================================================
    # CHECKOUT ENDPOINTS
    # ========================================================================
    
    # Checkout page - get cart and calculate taxes/fees
    path(
        'api/checkout/',
        views.CheckoutAPIView.as_view(),
        name='checkout'
    ),
    
    # Create order from cart
    path(
        'api/orders/create/',
        views.CreateOrderAPIView.as_view(),
        name='create_order'
    ),
    
    
    # ========================================================================
    # ORDER MANAGEMENT ENDPOINTS
    # ========================================================================
    
    # List user's orders (authenticated users only)
    path(
        'api/orders/',
        views.OrderListAPIView.as_view(),
        name='order_list'
    ),
    
    # Get order details by order number
    path(
        'api/orders/<str:order_number>/',
        views.OrderDetailAPIView.as_view(),
        name='order_detail'
    ),
    
    # Initiate payment for order
    path(
        'api/orders/<str:order_number>/pay/',
        views.InitiatePaymentAPIView.as_view(),
        name='initiate_payment'
    ),
    
    # Confirm order (admin only)
    path(
        'api/orders/<str:order_number>/confirm/',
        views.ConfirmOrderAPIView.as_view(),
        name='confirm_order'
    ),
    
    # Update order status (admin only)
    path(
        'api/orders/<str:order_number>/status/',
        views.UpdateOrderStatusAPIView.as_view(),
        name='update_order_status'
    ),
    
    # Cancel order
    path(
        'api/orders/<str:order_number>/cancel/',
        views.CancelOrderAPIView.as_view(),
        name='cancel_order'
    ),
    
]