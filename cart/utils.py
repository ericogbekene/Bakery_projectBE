from django.db import transaction
from decimal import Decimal
from django.db.models import Sum


def get_or_create_cart(request):
    """
    Get existing cart or create new one for user/guest.
    """
    # Import models inside function - only when needed
    from .models import Cart
    
    cart = None
    
    # Try to get cart for logged-in user
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        # If user has a session cart, merge it
        if 'cart_id' in request.session:
            session_cart = Cart.objects.filter(
                id=request.session['cart_id'],
                is_active=True
            ).first()
            
            if session_cart and session_cart != cart:
                cart = merge_carts(cart, session_cart)
                request.session.pop('cart_id', None)
    
    # For guests, use session
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(
                id=cart_id,
                session_key=request.session.session_key,
                is_active=True
            ).first()
    
    # Create new cart if none exists
    if not cart:
        cart = create_new_cart(request)
        request.session['cart_id'] = cart.id
    
    return cart


def create_new_cart(request):
    """
    Create a new cart for user or guest.
    """
    from .models import Cart
    
    cart = Cart()
    
    if request.user.is_authenticated:
        cart.user = request.user
    else:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        cart.session_key = request.session.session_key
    
    cart.save()
    return cart


@transaction.atomic
def merge_carts(user_cart, session_cart):
    """
    Merge guest session cart into user cart when user logs in.
    """
    # Import models inside function
    from .models import CartItem
    
    # If no user cart exists, convert session cart to user cart
    if not user_cart:
        session_cart.user = user_cart.user if user_cart else None
        session_cart.session_key = None
        session_cart.save()
        return session_cart
    
    # Merge items from session cart to user cart
    for session_item in session_cart.items.all():
        # Check if same product with same customization exists
        existing_item = user_cart.items.filter(
            product=session_item.product,
            flavour_1=session_item.flavour_1,
            flavour_2=session_item.flavour_2,
            size=session_item.size,
            colours=session_item.colours,
            cake_topper=session_item.cake_topper,
            candle=session_item.candle,
            birthday_card=session_item.birthday_card,
            chocolate=session_item.chocolate,
            wine=session_item.wine,
            whiskey_200ml=session_item.whiskey_200ml,
            additional_notes=session_item.additional_notes,
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += session_item.quantity
            existing_item.save()
            session_item.delete()
        else:
            # Move item to user cart
            session_item.cart = user_cart
            session_item.save()
    
    # Deactivate session cart
    session_cart.is_active = False
    session_cart.save()
    
    return user_cart


def get_cart_item_count(request):
    """
    Get total number of items in cart.
    """
    cart = get_or_create_cart(request)
    # Use aggregate instead of Python sum for efficiency
    result = cart.items.aggregate(total=Sum('quantity'))
    return result['total'] or 0


def get_cart_total(request):
    """
    Get total price of cart.
    """
    cart = get_or_create_cart(request)
    return cart.total_price


def clear_cart(request):
    """
    Clear all items from cart.
    """
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return cart


def remove_cart_item(request, cart_item_id):
    """
    Remove a specific item from cart.
    """
    from .models import CartItem
    
    try:
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        cart_item.delete()
        return cart_item
    except CartItem.DoesNotExist:
        return None


def get_cart_items_with_breakdown(request):
    """
    Get all cart items with detailed price breakdown.
    """
    cart = get_or_create_cart(request)
    items = []
    
    for cart_item in cart.items.all():
        items.append({
            'id': cart_item.id,
            'product': cart_item.product.name,
            'quantity': cart_item.quantity,
            'unit_price': str(cart_item.unit_price),
            'total_price': str(cart_item.total_item_price),
            'customization_breakdown': cart_item.get_customization_breakdown(),
            'customization_summary': cart_item.get_customization_summary(),
        })
    
    return {
        'items': items,
        'cart_total': str(cart.total_price),
        'item_count': cart.item_count,
    }