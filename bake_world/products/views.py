from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import routers, serializers, viewsets
from .models import Product, Category, Order
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer


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
    serializer_class = OrderSerializer 

