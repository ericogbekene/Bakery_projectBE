from rest_framework import serializers
from .models import Order

class OrderCreateSerializer(serializers.ModelSerializer):
    class   Meta:
        model = Order
        fields = [
            'first_name',
            'last_name',
            'email',
            'address',
            'city'
        ]