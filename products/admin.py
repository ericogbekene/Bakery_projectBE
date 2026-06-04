from django.contrib import admin
from django import forms
from .models import Category, Product
from django.utils.html import format_html


class ProductAdminForm(forms.ModelForm):
    """Custom form for Product admin to conditionally show/hide fields."""
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide cake-specific fields initially
        cake_fields = ['layers', 'covering', 'inspiration', 'preparation_days']
        for field in cake_fields:
            self.fields[field].widget.attrs['class'] = 'cake-field'
        
        # Add JavaScript to show/hide fields based on product_type
        # This will be handled by JavaScript in the admin template


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'image_preview']
    search_fields = ['name']
    readonly_fields = ['slug', 'image_preview']

    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug', 'description']
        }),
        ('Image', {
            'fields': ['image', 'image_preview']
        }),
    ]

   

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" height="50" />', obj.image_url)
        return 'No image'
    image_preview.short_description = 'Preview'

    def product_count(self, obj):
        return obj.products.filter(available=True).count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['name', 'product_type', 'category', 'price', 'available', 'created_at']
    list_filter = ['product_type', 'category', 'available', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['available', 'price']
    
    # Fields organization
    fieldsets = [
        ('Basic Information', {
            'fields': ['product_type', 'name', 'slug', 'category', 'image', 'description', 'price', 'available']
        }),
        ('Cake Details (Only for Cakes)', {
            'fields': ['layers', 'covering', 'inspiration', 'preparation_days'],
            'classes': ['collapse'],  # Makes this section collapsible
        }),
    ]
    
    # Add custom JavaScript for conditional fields
    class Media:
        js = ('admin/js/product_admin.js',)  # We'll create this file
    
    def get_form(self, request, obj=None, **kwargs):
        """Dynamically adjust form based on product_type."""
        form = super().get_form(request, obj, **kwargs)
        
        # If editing an existing product that's a pastry, make cake fields read-only
        if obj and obj.product_type == 'pastry':
            cake_fields = ['layers', 'covering', 'inspiration', 'preparation_days']
            for field in cake_fields:
                if field in form.base_fields:
                    form.base_fields[field].disabled = True
                    form.base_fields[field].required = False
        
        return form


