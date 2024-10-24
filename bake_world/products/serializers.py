'''
Insert serializers here
'''
from .models import Product, Category, Order
from rest_framework import serializers



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category #NOT "Category"
        fields = ["id", "name", "slug"]

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product #NOT "Product"
        fields = [
            "name", "slug", "description", "price", "quantity", "available", "created_at", "updated_at", "category", "image"
        ]
    
    """ 
    Method to create a new Product
    """
    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                product = Product.objects.create(category=category, **validated_data)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Invalid category_id")
        else:
            product = Product.objects.create(**validated_data)
        return product

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'quantity', 'created_at', 'updated_at']
        