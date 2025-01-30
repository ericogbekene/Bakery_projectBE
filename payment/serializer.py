from rest_framework import serializers

class PaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10000, decimal_places=2)
    email = serializers.EmailField()