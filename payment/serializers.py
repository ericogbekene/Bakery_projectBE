from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model, including a method 
    field for human-readable status.
    """
    
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'flutterwave_transaction_id',
            'order',
            'email',
            'amount',
            'currency',
            'status',
            'status_display',
            'created_at',
            'modified_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'status_display',
            'flutterwave_transaction_id',
            'created_at',
            'modified_at',
        ]

    # Fixed: properly indented outside Meta
    def get_status_display(self, obj):
        return obj.get_status_display()


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a payment.
    Validates the order number before creating a transaction.
    """
    order_number = serializers.CharField(max_length=50)


class VerifyPaymentSerializer(serializers.Serializer):
    """
    Serializer for verifying a payment after redirect.
    """
    transaction_id = serializers.CharField()
    tx_ref = serializers.CharField()
    status = serializers.CharField()


class RefundPaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a refund.
    """
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )