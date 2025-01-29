from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'email',
            'amount',
            'reference',
            'status',
            'timestamp']
        read_only_fields = ['status', 'timestamp']
        
        def get_status(self, obj):
            return obj.get_status_display()