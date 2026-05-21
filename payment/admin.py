from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'reference',
        'email',
        'amount',
        'currency',
        'status',
        'order',
        'flutterwave_transaction_id',
        'created_at',
    )
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('email', 'reference', 'flutterwave_transaction_id', 'order__order_number')
    readonly_fields = (
        'reference',
        'flutterwave_transaction_id',
        'order',
        'cart',
        'email',
        'amount',
        'currency',
        'user',
        'created_at',
        'modified_at',
    )
    actions = ['mark_as_refunded']

    fieldsets = [
        ('Transaction Info', {
            'fields': ['reference', 'flutterwave_transaction_id', 'status']
        }),
        ('Customer', {
            'fields': ['user', 'email']
        }),
        ('Payment Details', {
            'fields': ['amount', 'currency', 'order', 'cart']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'modified_at'],
            'classes': ['collapse']
        }),
    ]

    @admin.action(description="Mark selected transactions as refunded")
    def mark_as_refunded(self, request, queryset):
        queryset.update(status='refunded')

    def has_add_permission(self, request):
        # Transactions should only be created programmatically, not via admin
        return False

    def has_change_permission(self, request, obj=None):
        # Transactions should not be manually edited — only status via actions
        return False

    def has_delete_permission(self, request, obj=None):
        # Payment records should never be deleted
        return False