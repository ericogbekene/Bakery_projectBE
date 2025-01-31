from rest_framework import serializers
from .models import Order, OrderItem


class OrderCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254, required=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'address',
            'city',
            'created',
            'updated',
            'paid',
            'total_cost'
        ]
        read_only_fields = ['id', 'created', 'updated', 'paid', 'total_cost']

    def validate_first_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long.")
        return value.capitalize()

    def validate_last_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long.")
        return value.capitalize()

    def validate_city(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("City name must be at least 2 characters long.")
        return value.capitalize()

    def validate_address(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Address must be at least 5 characters long.")
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value

    def create(self, validated_data):
        """
        Create and return a new Order instance.

        This method creates a new Order instance using the validated data
        provided by the serializer.

        Parameters:
        validated_data (dict): A dictionary of validated data containing the
                               attributes for the new Order instance.

        Returns:
        Order: The newly created Order instance.
        """
        return Order.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing Order instance, given the validated data.

        This method updates the attributes of an existing Order instance with the
        values provided in the validated_data dictionary. It then saves the updated
        instance to the database.

        Parameters:
        instance (Order): The existing Order instance to be updated.
        validated_data (dict): A dictionary of validated data containing the new values
                               for the Order instance's attributes.

        Returns:
        Order: The updated Order instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items.
    """
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for orders, including related order items.
    """
    items = OrderItemSerializer(many=True, read_only=True)  # Include order items

    class Meta:
        model = Order
        fields = ['id', 'first_name', 'last_name', 'email', 'address', 'city',
                  'created', 'updated', 'total_cost', 'paid', 'items']
