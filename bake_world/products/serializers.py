'''
Insert serializers here
'''
from .models import Product, Category
from rest_framework import serializers



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = 'Category'
        fields = ["name", "slug"]

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = 'Product'
        fields = [
            "name", "slug", "descrption", "price", "quantity", "available", "created_at", "updated_at", "category", "image"
        ]
        