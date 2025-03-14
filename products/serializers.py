from .models import Product, Category
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "available", "created_at", "updated_at", "category", "image"
        ]
