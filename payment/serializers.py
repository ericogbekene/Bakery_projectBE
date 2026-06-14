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
            'paystack_transaction_id',
            'paystack_access_code',
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
            'paystack_transaction_id',
            'paystack_access_code',
            'created_at',
            'modified_at',
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a Paystack payment.
    Validates the order number before creating a transaction.
    """
    order_number = serializers.CharField(max_length=50)


class VerifyPaymentSerializer(serializers.Serializer):
    """
    Serializer for verifying a Paystack payment after redirect.
    Paystack returns 'reference' and 'trxref' as query parameters.
    """
    reference = serializers.CharField()
    trxref = serializers.CharField(required=False)


class RefundPaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a refund via Paystack.
    """
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )