from rest_framework import serializers


class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=True)
    override_quantity = serializers.BooleanField(default=False)