from decimal import Decimal
from django.conf import settings
from products.models import Product
from products.serializers import ProductListSerializer

class Cart:
    def __init__(self, request=None):
        """
        Initialize the cart with the session.
        """
        self.session = request.session if request else {}  # Initialize session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart  # Store cart data in session

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        """ Mark the session as modified to make sure it gets saved """
        if hasattr(self.session, 'modified'):
            self.session.modified = True  # Mark session as modified to save changes

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        self.cart.pop(product_id, None)  # Avoids KeyError if not present
        self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and retrieve products from the database.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            product_data = ProductSerializer(product).data  # Serialize the product
            cart[str(product.id)].update({'product': product_data, 'product_id': product.id})

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Return total quantity of items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total price of items in the cart.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
    
    def get_discount(self):
        """
        Calculate and return the discount for the cart.
        This can be based on a session key or a fixed discount for testing purposes.
        """
        discount = Decimal(0)  # Default to no discount

        # Example logic for a simple discount (replace with real coupon code logic)
        if 'DISCOUNT_CODE' in self.session:
            discount_code = self.session['DISCOUNT_CODE']
            if discount_code == 'SAVE10':
                discount = Decimal(10)  # Apply a fixed $10 discount

        return discount

    def get_total_price_after_discount(self):
        """
        Get the total price after applying any discounts.
        """
        discount = self.get_discount()
        return self.get_total_price() - discount
    

    def clear(self):
        """
        Remove cart from session.
        """
        self.session.pop(settings.CART_SESSION_ID, None)  # Remove cart data from session
        self.save()  # Ensure session changes are saved
