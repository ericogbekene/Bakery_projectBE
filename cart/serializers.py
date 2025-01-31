from rest_framework import serializers
from products.models import Product






class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=True)
    override_quantity = serializers.BooleanField(default=False)


class CartDetailSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)



class CartRemoveSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        """
        Validate that the product exists before removal.
        """
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid product ID. Product does not exist.")
        return value
