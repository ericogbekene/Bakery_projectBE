# cart/admin.py
from django.contrib import admin
from django import forms
from .models import (
    CakeCustomizationOption, CakeSizeMultiplier, 
    CakeFlavorPrice, Cart, CartItem, DeliveryInfo
)
from decimal import Decimal


@admin.register(CakeCustomizationOption)
class CakeCustomizationOptionAdmin(admin.ModelAdmin):
    list_display = ['customization_type', 'price_per_unit', 'is_active', 'description']
    list_editable = ['price_per_unit', 'is_active']
    list_filter = ['is_active', 'customization_type']
    search_fields = ['customization_type', 'description']
    ordering = ['customization_type']
    
    fieldsets = [
        ('Customization Type', {
            'fields': ['customization_type', 'description']
        }),
        ('Pricing', {
            'fields': ['price_per_unit', 'is_active']
        }),
    ]


@admin.register(CakeSizeMultiplier)
class CakeSizeMultiplierAdmin(admin.ModelAdmin):
    list_display = ['size', 'get_size_display', 'multiplier']
    list_editable = ['multiplier']
    ordering = ['size']
    
    def get_size_display(self, obj):
        return dict(obj.CAKE_SIZES).get(obj.size, obj.size)
    get_size_display.short_description = 'Size Display'
    get_size_display.admin_order_field = 'size'


@admin.register(CakeFlavorPrice)
class CakeFlavorPriceAdmin(admin.ModelAdmin):
    list_display = ['flavor', 'price_multiplier', 'is_active']
    list_editable = ['price_multiplier', 'is_active']
    list_filter = ['is_active']
    ordering = ['flavor']


class CartItemInline(admin.TabularInline):
    model = CartItem
    fields = ['product', 'quantity', 'size', 'flavour_1', 'flavour_2', 
              'unit_price', 'total_item_price']
    readonly_fields = ['unit_price', 'total_item_price']
    extra = 0
    can_delete = True
    
    def unit_price(self, obj):
        return obj.unit_price
    unit_price.short_description = 'Unit Price'
    
    def total_item_price(self, obj):
        return obj.total_item_price
    total_item_price.short_description = 'Total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'is_active', 'item_count', 
                   'subtotal', 'delivery_cost', 'grand_total', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'session_key']
    readonly_fields = ['created_at', 'updated_at', 'subtotal', 'delivery_cost', 'grand_total']
    inlines = [CartItemInline]
    
    fieldsets = [
        ('Cart Owner', {
            'fields': ['user', 'session_key']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
        ('Totals', {
            'fields': ['subtotal', 'delivery_cost', 'grand_total']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'
    
    def delivery_cost(self, obj):
        return obj.delivery_cost
    delivery_cost.short_description = 'Delivery'
    
    def grand_total(self, obj):
        return obj.grand_total
    grand_total.short_description = 'Grand Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'size', 'flavour_1', 
                   'unit_price', 'total_item_price', 'added_at']
    list_filter = ['added_at', 'size']
    search_fields = ['product__name', 'additional_notes']
    readonly_fields = ['unit_price', 'total_item_price', 'added_at', 
                      'size_multiplier_value', 'flavor_multiplier_value']
    
    fieldsets = [
        ('Product', {
            'fields': ['cart', 'product', 'quantity']
        }),
        ('Cake Customization', {
            'fields': [
                ('flavour_1', 'flavour_2'),
                'size',
                'colours',
                ('cake_topper', 'candle', 'birthday_card'),
                ('chocolate', 'wine', 'whiskey_200ml'),
                'additional_notes'
            ]
        }),
        ('Pricing Snapshots', {
            'fields': ['base_price', 'customization_cost']
        }),
        ('Calculated Prices', {
            'fields': [
                'size_multiplier_value',
                'flavor_multiplier_value',
                'unit_price',
                'total_item_price'
            ]
        }),
        ('Timestamps', {
            'fields': ['added_at']
        }),
    ]
    
    def size_multiplier_value(self, obj):
        return obj.size_multiplier_value
    size_multiplier_value.short_description = 'Size Multiplier'
    
    def flavor_multiplier_value(self, obj):
        return obj.flavor_multiplier_value
    flavor_multiplier_value.short_description = 'Flavor Multiplier'


@admin.register(DeliveryInfo)
class DeliveryInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'full_name', 'phone', 'delivery_date', 'calculated_fee']
    list_filter = ['delivery_date', 'state', 'city']
    search_fields = ['full_name', 'email', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Cart Reference', {
            'fields': ['cart']
        }),
        ('Customer Information', {
            'fields': ['full_name', 'email', 'phone']
        }),
        ('Delivery Address', {
            'fields': ['address', 'city', 'state', 'postal_code']
        }),
        ('Delivery Schedule', {
            'fields': ['delivery_date', 'delivery_time_slot']
        }),
        ('Pricing', {
            'fields': ['calculated_fee']
        }),
        ('Additional Information', {
            'fields': ['special_instructions']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]