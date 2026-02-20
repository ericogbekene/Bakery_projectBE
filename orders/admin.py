from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.timezone import now
from .models import (
    Order, OrderItem, OrderDelivery, 
    OrderHistory, OrderPayment
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'quantity', 'size', 'flavour_1', 'flavour_2',
              'unit_price', 'item_total']
    readonly_fields = ['product', 'quantity', 'size', 'flavour_1', 'flavour_2',
                      'unit_price', 'item_total']
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class OrderDeliveryInline(admin.StackedInline):
    model = OrderDelivery
    fieldsets = [
        ('Delivery Address', {
            'fields': ['address', 'city', 'state', 'postal_code']
        }),
        ('Delivery Schedule', {
            'fields': ['delivery_date', 'delivery_time_slot']
        }),
        ('Delivery Pricing', {
            'fields': ['delivery_zone', 'delivery_fee']
        }),
        ('Delivery Status', {
            'fields': ['is_delivered', 'delivered_at', 'delivery_notes']
        }),
        ('Instructions', {
            'fields': ['special_instructions']
        }),
    ]
    readonly_fields = ['delivery_zone', 'delivery_fee', 'created_at', 'updated_at']
    extra = 0


class OrderHistoryInline(admin.TabularInline):
    model = OrderHistory
    fields = ['action', 'description', 'changed_by', 'timestamp', 'old_value', 'new_value']
    readonly_fields = ['action', 'description', 'changed_by', 'timestamp', 'old_value', 'new_value']
    extra = 0
    can_delete = False
    ordering = ['-timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    fields = ['transaction_id', 'amount', 'payment_method', 'status', 'processed_at']
    readonly_fields = ['transaction_id', 'amount', 'payment_method', 'status', 'processed_at']
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_info', 'order_total', 
        'status_colored', 'payment_status_colored', 'flutterwave_reference_display', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'delivery__city']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone', 
                     'flutterwave_transaction_id', 'flutterwave_reference']
    readonly_fields = [
        'order_number', 'user', 'cart', 'subtotal', 'delivery_fee', 'total_amount',
        'payment_method',  # Add this as readonly since it's non-editable
        'flutterwave_transaction_id', 'flutterwave_reference', 'flutterwave_response',
        'created_at', 'updated_at', 'confirmed_at', 'processing_at',
        'ready_at', 'completed_at', 'cancelled_at'
    ]
    inlines = [
        OrderDeliveryInline,
        OrderItemInline,
        OrderPaymentInline,
        OrderHistoryInline
    ]
    
    fieldsets = [
        ('Order Information', {
            'fields': ['order_number', 'user', 'cart']
        }),
        ('Customer Information', {
            'fields': [
                'customer_name', 'customer_email', 'customer_phone',
                'guest_email', 'guest_phone'
            ]
        }),
        ('Pricing', {
            'fields': ['subtotal', 'delivery_fee', 'total_amount']
        }),
        ('Order Status', {
            'fields': [
                'status', 
                'confirmed_at', 'processing_at', 'ready_at', 
                'completed_at', 'cancelled_at', 'cancellation_reason'
            ]
        }),
        ('Payment Information - Flutterwave', {
            'fields': [
                'payment_status', 
                'payment_method',  # Will show as read-only
                'flutterwave_transaction_id',
                'flutterwave_reference',
                'payment_date'
            ]
        }),
        ('Flutterwave Response Data', {
            'fields': ['flutterwave_response'],
            'classes': ['collapse']  # Collapsed by default since it's JSON
        }),
        ('Admin Notes', {
            'fields': ['admin_notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_ready', 
               'mark_as_completed', 'mark_as_cancelled']
    
    def customer_info(self, obj):
        return f"{obj.customer_name}\n{obj.customer_phone}"
    customer_info.short_description = 'Customer'
    
    def order_total(self, obj):
        return f"₦{obj.total_amount:,.2f}"
    order_total.short_description = 'Total'
    
    def flutterwave_reference_display(self, obj):
        """Display Flutterwave reference with link if available"""
        if obj.flutterwave_reference:
            return format_html(
                '<span style="font-family: monospace;">{}</span>',
                obj.flutterwave_reference[:15] + '...' if len(obj.flutterwave_reference) > 15 else obj.flutterwave_reference
            )
        return '-'
    flutterwave_reference_display.short_description = 'Flutterwave Ref'
    
    def status_colored(self, obj):
        color = obj.get_status_display_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def payment_status_colored(self, obj):
        color = obj.get_payment_status_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_colored.short_description = 'Payment'
    
    # Actions
    def mark_as_confirmed(self, request, queryset):
        for order in queryset:
            order.update_status('confirmed', request.user)
        self.message_user(request, f"{queryset.count()} order(s) marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected orders as Confirmed"
    
    def mark_as_processing(self, request, queryset):
        for order in queryset:
            order.update_status('processing', request.user)
        self.message_user(request, f"{queryset.count()} order(s) marked as processing.")
    mark_as_processing.short_description = "Mark selected orders as Processing"
    
    def mark_as_ready(self, request, queryset):
        for order in queryset:
            order.update_status('ready', request.user)
        self.message_user(request, f"{queryset.count()} order(s) marked as ready.")
    mark_as_ready.short_description = "Mark selected orders as Ready"
    
    def mark_as_completed(self, request, queryset):
        for order in queryset:
            order.update_status('completed', request.user)
        self.message_user(request, f"{queryset.count()} order(s) marked as completed.")
    mark_as_completed.short_description = "Mark selected orders as Completed"
    
    def mark_as_cancelled(self, request, queryset):
        for order in queryset:
            order.update_status('cancelled', request.user, "Cancelled via admin")
        self.message_user(request, f"{queryset.count()} order(s) marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"


@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = ['order', 'city', 'delivery_date', 'delivery_fee', 'is_delivered']
    list_filter = ['city', 'delivery_date', 'is_delivered']
    search_fields = ['order__order_number', 'address', 'city']
    readonly_fields = ['created_at', 'updated_at', 'delivered_at']
    
    fieldsets = [
        ('Order', {
            'fields': ['order']
        }),
        ('Address', {
            'fields': ['address', 'city', 'state', 'postal_code']
        }),
        ('Schedule', {
            'fields': ['delivery_date', 'delivery_time_slot']
        }),
        ('Pricing', {
            'fields': ['delivery_zone', 'delivery_fee']
        }),
        ('Delivery Status', {
            'fields': ['is_delivered', 'delivered_at', 'delivery_notes']
        }),
        ('Instructions', {
            'fields': ['special_instructions']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'size', 'unit_price', 'item_total']
    list_filter = ['size', 'created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Order Reference', {
            'fields': ['order', 'product']
        }),
        ('Quantity', {
            'fields': ['quantity']
        }),
        ('Customization', {
            'fields': [
                ('flavour_1', 'flavour_2'),
                'size',
                'colours',
                ('cake_topper', 'candle', 'birthday_card'),
                ('chocolate', 'wine', 'whiskey_200ml'),
                'additional_notes'
            ]
        }),
        ('Pricing', {
            'fields': ['base_price', 'customization_cost', 'unit_price', 'item_total']
        }),
        ('Timestamps', {
            'fields': ['created_at']
        }),
    ]


@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'action', 'changed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['order__order_number', 'description']
    readonly_fields = ['order', 'action', 'description', 'changed_by', 
                      'timestamp', 'old_value', 'new_value']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'amount', 'payment_method', 'status', 'processed_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'order__order_number', 'reference_number']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    
    fieldsets = [
        ('Order Reference', {
            'fields': ['order']
        }),
        ('Payment Details', {
            'fields': ['amount', 'payment_method', 'transaction_id', 'reference_number']
        }),
        ('Status', {
            'fields': ['status', 'processed_at']
        }),
        ('Notes', {
            'fields': ['notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]