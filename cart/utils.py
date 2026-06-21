from django.db import transaction
from django.db.models import Sum
from django.db.utils import IntegrityError


def get_or_create_cart(request):
    """
    Get existing cart or create new one for user/guest.

    For authenticated users: returns their active cart.
    For guests: returns cart linked to session key.
    Handles merging of guest cart to user cart on login.
    """
    from .models import Cart

    cart = None

    print("=" * 50)
    print("ADD TO CART")
    print("SESSION KEY:", request.session.session_key)
    print("SESSION CART ID:", request.session.get('cart_id'))
    print("=" * 50)

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

        # ✅ FIX: Fall back to looking up by session_key alone, in case
        # 'cart_id' wasn't present in THIS request's session dict yet
        # (e.g. a concurrent sibling request created the cart a moment
        # ago and committed it to the DB, but this request's in-memory
        # session object was loaded before that write happened). Without
        # this fallback, a second concurrent request would blindly try to
        # create a *second* cart/session row for the same browser tab,
        # which is what was driving the session race.
        if not cart and request.session.session_key:
            cart = Cart.objects.filter(
                session_key=request.session.session_key,
                is_active=True
            ).order_by('-id').first()

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

    if request.user.is_authenticated:
        cart = Cart(user=request.user)
        cart.save()
        return cart

    # ✅ FIX: Don't manually force a session row write here on its own.
    # Forcing request.session.create() (or even a bare .save()) mid-view,
    # with no further guard, let two near-simultaneous guest requests
    # (e.g. the cart-count poll firing alongside an order POST on first
    # page load, before any sessionid cookie exists) each generate their
    # own session_key and each try to persist/overwrite the same session
    # row, producing "Forced update did not affect any rows" ->
    # SessionInterrupted.
    #
    # We still need a session_key to associate the cart row with before
    # the response is returned, so we save once here — but we now follow
    # it with a guarded get_or_create against the DB (below), so even if
    # two requests still race and end up with two different session keys
    # momentarily, we don't blow up: we simply get/create a cart per key
    # and the harmless duplicate gets reconciled on the next request via
    # the session_key fallback lookup in get_or_create_cart above.
    if not request.session.session_key:
        request.session.save()

    session_key = request.session.session_key

    try:
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(
                session_key=session_key,
                is_active=True,
            )
    except IntegrityError:
        # Last-resort race: another request committed a cart for this
        # exact session_key between our check and insert. Re-fetch it
        # instead of erroring out.
        cart = Cart.objects.filter(
            session_key=session_key,
            is_active=True
        ).order_by('-id').first()

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