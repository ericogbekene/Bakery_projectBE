from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import  viewsets
from .models import Product, Category, Order, OrderItem, Cart, CartItem
from .serializers import (ProductSerializer, 
                          CategorySerializer, 
                          OrderSerializer, 
                          CreateOrderSerializer, 
                          CreateOrderItemSerializer, 
                          OrderItemSerializer,
                          CreateCartSerializer,
                          CreateCartItemSerializer
                          
                          
                          
                    
)


# Create your views here.

def products(request):
    return HttpResponse("Hello world!")


# Create Viewsets for pages here

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category ViewSet
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'  # Use slug instead of id for lookup


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product ViewSet
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'  # Use slug instead of id for lookup

    def get_queryset(self):
        """
        Filter products by category
        """
        category_slug = self.request.query_params.get('category_slug')
        if category_slug:
            return Product.objects.filter(category__slug=category_slug)
        return Product.objects.all()


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order ViewSet
    """
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Order Item ViewSet
    """
    queryset = OrderItem.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderItemSerializer
        return OrderItemSerializer


class CartViewSet(viewsets.ModelViewSet):
    """
    Cart ViewSet
    """
    queryset = Cart.objects.all()
    serializer_class = CreateCartSerializer
    
class CartItemViewSet(viewsets.ModelViewSet):
    """
    Cart Item ViewSet
    """
    queryset = CartItem.objects.all()
    serializer_class = CreateCartItemSerializer