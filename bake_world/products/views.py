from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponse

from .models import Product, Category, Order
from .serializers import ProductSerializer, CategorySerializer
from rest_framework import routers, serializers, viewsets

def products(request):
    return HttpResponse("Hello world!")

"""
Create Viewsets for pages here

E.g 
- Product Listing
- Filter By Category

"""

class CategoryViewSet(viewsets.ModelViewSet):
    """
    queryset 
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    queryset 
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer