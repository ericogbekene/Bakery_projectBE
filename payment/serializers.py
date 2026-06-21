from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model, including a method 
    field for human-readable status.
    """
    
    status_display = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'reference',
            'paystack_transaction_id',
            'paystack_access_code',
            'order',
            'order_number',
            'customer_name',
            'customer_email',
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
        """Get human-readable status."""
        return obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status

    def get_order_number(self, obj):
        """Get order number from related order."""
        if obj.order:
            return obj.order.order_number
        return None

    def get_customer_name(self, obj):
        """Get customer name from related order."""
        if obj.order:
            return obj.order.customer_name
        return None

    def get_customer_email(self, obj):
        """Get customer email from related order."""
        if obj.order:
            return obj.order.customer_email
        return obj.email


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a Paystack payment.
    Validates the order number before creating a transaction.
    """
    order_number = serializers.CharField(max_length=50, required=True)

    def validate_order_number(self, value):
        """Validate that the order number is provided."""
        if not value or not value.strip():
            raise serializers.ValidationError("Order number is required.")
        return value.strip()


class VerifyPaymentSerializer(serializers.Serializer):
    """
    Serializer for verifying a Paystack payment after redirect.
    Paystack returns 'reference' and 'trxref' as query parameters.
    """
    reference = serializers.CharField(required=False, allow_blank=True)
    trxref = serializers.CharField(required=False, allow_blank=True)
    
    # Response fields
    status = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    details = serializers.JSONField(required=False)
    transaction = serializers.JSONField(required=False)
    expected_amount_kobo = serializers.IntegerField(required=False)
    actual_amount_kobo = serializers.IntegerField(required=False)

    def validate(self, data):
        """
        Validate that at least one reference is provided.
        """
        reference = data.get('reference')
        trxref = data.get('trxref')
        
        # For request validation - at least one reference is required
        if not reference and not trxref:
            raise serializers.ValidationError(
                "Either 'reference' or 'trxref' is required."
            )
        
        # If both are provided, use reference as the primary
        if reference and not trxref:
            data['reference'] = reference
        elif trxref and not reference:
            data['reference'] = trxref
        # If both are provided, reference is already set
        
        return data

    def to_representation(self, instance):
        """
        Customize the representation of the serializer.
        This is used when serializing the response.
        """
        # If instance is a dict (for response), return as is
        if isinstance(instance, dict):
            return instance
        
        # If instance is a Transaction object, serialize it
        if hasattr(instance, 'reference'):
            return {
                'status': 'success',
                'message': 'Payment verified successfully.',
                'transaction': TransactionSerializer(instance).data
            }
        
        return super().to_representation(instance)


class RefundPaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a refund via Paystack.
    """
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default="Customer request"
    )

    def validate_reason(self, value):
        """Validate and clean the reason field."""
        if value and not value.strip():
            return "Customer request"
        return value or "Customer request"