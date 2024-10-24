from .models import Product, Category, Order, OrderItem
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "quantity", "available", "created_at", "updated_at", "category", "image"
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "quantity", "created_at", "updated_at", "items"]


class CreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "quantity", "created_at", "updated_at"]

    def create(self, validated_data):
        order = Order.objects.create(**validated_data)
        return order


class CreateOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity"]

    def create(self, validated_data):
        order_item = OrderItem.objects.create(**validated_data)
        return order_item