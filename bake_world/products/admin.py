from django.contrib import admin

from .models import Product, Category, Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class OrderAdmin(admin.ModelAdmin): 
    inlines = [OrderItemInline]
    list_display = ('id', 'user', 'quantity', 'created_at', 'updated_at')

class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ('id', 'user', 'created_at', 'updated_at')

admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)


admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Order)

# Register your models here.
