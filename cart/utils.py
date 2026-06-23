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
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(
                id=cart_id,
                session_key=request.session.session_key,
                is_active=True
            ).first()

        # Fall back to session_key lookup in case of concurrent requests
        if not cart and request.session.session_key:
            cart = Cart.objects.filter(
                session_key=request.session.session_key,
                is_active=True
            ).order_by('-id').first()

    if not cart:
        cart = create_new_cart(request)
        request.session['cart_id'] = cart.id

    return cart


def get_cart_if_exists(request):
    """
    Look up the current cart WITHOUT creating one if it doesn't exist.
    Used by count/summary endpoints to avoid ghost cart creation.
    """
    from .models import Cart

    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user, is_active=True).first()

    # Guest — try cart_id in session first
    cart_id = request.session.get('cart_id')
    if cart_id and request.session.session_key:
        cart = Cart.objects.filter(
            id=cart_id,
            session_key=request.session.session_key,
            is_active=True
        ).first()
        if cart:
            return cart

    # Fall back to session_key lookup
    if request.session.session_key:
        return Cart.objects.filter(
            session_key=request.session.session_key,
            is_active=True
        ).order_by('-id').first()

    return None


def create_new_cart(request):
    """
    Create a new cart for user or guest.
    """
    from .models import Cart

    if request.user.is_authenticated:
        cart = Cart(user=request.user)
        cart.save()
        return cart

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
        cart = Cart.objects.filter(
            session_key=session_key,
            is_active=True
        ).order_by('-id').first()

    return cart


@transaction.atomic
def merge_carts(user_cart, session_cart, user):
    """
    Merge guest session cart into user cart when user logs in.
    """
    from .models import CartItem

    if not user_cart:
        session_cart.user = user
        session_cart.session_key = None
        session_cart.save()
        return session_cart

    for session_item in session_cart.items.all():
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
            existing_item.quantity += session_item.quantity
            existing_item.save()
            session_item.delete()
        else:
            session_item.cart = user_cart
            session_item.save()

    session_cart.is_active = False
    session_cart.save()

    return user_cart


def get_cart_item_count(request):
    """
    Get total number of items in cart without creating one if it doesn't exist.
    """
    cart = get_cart_if_exists(request)
    if not cart:
        return 0
    result = cart.items.aggregate(total=Sum('quantity'))
    return result['total'] or 0


def clear_cart(request):
    """
    Clear all items from cart.
    """
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return cart