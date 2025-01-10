from django.contrib import admin

from .models import Product, Category, Order, OrderItem, Cart, CartItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name',]
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'price',
        'available',
        'created_at',
        'updated_at'

    ]
    list_filter = ['available', 'created_at', 'updated_at', 'price']
    list_editable = ['price', 'available']
    prepopulated_fields = {'slug': ('name',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class OrderAdmin(admin.ModelAdmin): 
    inlines = [OrderItemInline]
    list_display = ('id', 'quantity', 'created_at', 'updated_at')

class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ('id', 'created_at', 'updated_at')

admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)



# Register your models here.
