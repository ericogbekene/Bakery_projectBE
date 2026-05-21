from django.db import transaction
from django.db.models import Sum


def get_or_create_cart(request):
    """
    Get existing cart or create new one for user/guest.

    For authenticated users: returns their active cart.
    For guests: returns cart linked to session key.
    Handles merging of guest cart to user cart on login.
    """
    from .models import Cart

    cart = None

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()

        # If user has a session cart, merge it into their user cart
        if 'cart_id' in request.session:
            session_cart = Cart.objects.filter(
                id=request.session['cart_id'],
                is_active=True
            ).first()

            if session_cart and session_cart != cart:
                cart = merge_carts(cart, session_cart, request.user)
                request.session.pop('cart_id', None)

    else:
        # For guests, look up cart by session
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
        if not request.session.session_key:
            request.session.create()
        cart.session_key = request.session.session_key

    cart.save()
    return cart


@transaction.atomic
def merge_carts(user_cart, session_cart, user):
    """
    Merge guest session cart into user cart when user logs in.

    Fixed: now accepts 'user' as an explicit parameter so the guest cart
    can be correctly assigned to the user when no user cart exists yet.

    Args:
        user_cart: Cart instance for user (can be None)
        session_cart: Guest cart instance from session
        user: The authenticated user to assign the cart to

    Returns:
        Cart instance (either merged or converted)
    """
    from .models import CartItem

    # If no user cart exists, convert the session cart into the user's cart
    if not user_cart:
        session_cart.user = user  # Fixed: was incorrectly assigning None
        session_cart.session_key = None
        session_cart.save()
        return session_cart

    # Merge items from session cart into user cart
    for session_item in session_cart.items.all():
        # Check if same product with same customization already exists in user cart
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
            # Add quantities together
            existing_item.quantity += session_item.quantity
            existing_item.save()
            session_item.delete()
        else:
            # Move item to user cart
            session_item.cart = user_cart
            session_item.save()

    # Deactivate the now-empty session cart
    session_cart.is_active = False
    session_cart.save()

    return user_cart


def get_cart_item_count(request):
    """
    Get total number of items in cart (sum of all quantities).
    Uses aggregate for efficiency — avoids N+1 query.
    """
    cart = get_or_create_cart(request)
    result = cart.items.aggregate(total=Sum('quantity'))
    return result['total'] or 0


def clear_cart(request):
    """
    Clear all items from cart.
    Returns the now-empty cart instance.
    """
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return cart