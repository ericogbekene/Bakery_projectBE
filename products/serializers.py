from rest_framework import serializers
from .models import Category, Product
from django.utils.text import slugify


class CategoryListSerializer(serializers.ModelSerializer):
    """Serializer for category list view with minimal fields."""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count']
        read_only_fields = ['slug']
    
    def get_product_count(self, obj):
        """Return count of available products in this category."""
        return obj.products.filter(available=True).count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Serializer for category detail view with all fields."""
    products = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'product_count', 'products'
        ]
        read_only_fields = ['slug']
    
    def get_products(self, obj):
        """Return available products in this category."""
        products = obj.products.filter(available=True)[:10]  # Limit to 10
        return ProductListSerializer(products, many=True, context=self.context).data
    
    def get_product_count(self, obj):
        """Return count of available products in this category."""
        return obj.products.filter(available=True).count()


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating categories."""
    
    class Meta:
        model = Category
        fields = ['name', 'slug']
    
    def create(self, validated_data):
        # Slug will be auto-generated in the model's save method
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Regenerate slug if name changes
        if 'name' in validated_data and validated_data['name'] != instance.name:
            instance.slug = slugify(validated_data['name'])
        return super().update(instance, validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view with essential fields."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'price', 'available',
            'category_name', 'stock_quantity', 'is_in_stock', 'is_low_stock',
            'created_at'
        ]
        read_only_fields = ['slug', 'created_at', 'is_in_stock', 'is_low_stock']
    
    def get_is_in_stock(self, obj):
        """Check if product is in stock."""
        return obj.is_in_stock()
    
    def get_is_low_stock(self, obj):
        """Check if product has low stock."""
        return obj.is_low_stock()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view with all fields."""
    category = CategoryListSerializer(read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'description', 'price', 'available',
            'stock_quantity', 'low_stock_threshold', 'track_inventory',
            'is_in_stock', 'is_low_stock', 'category', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'slug', 'created_at', 'updated_at', 'is_in_stock', 'is_low_stock'
        ]
    
    def get_is_in_stock(self, obj):
        """Check if product is in stock."""
        return obj.is_in_stock()
    
    def get_is_low_stock(self, obj):
        """Check if product has low stock."""
        return obj.is_low_stock()


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=True)
    
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'image', 'description', 'price', 'available',
            'stock_quantity', 'low_stock_threshold', 'track_inventory'
        ]
    
    def validate(self, data):
        """Cross-field validation."""
        # Ensure category exists if provided
        if 'category' in data:
            try:
                category = Category.objects.get(id=data['category'].id)
                data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({
                    'category': 'Category with this ID does not exist.'
                })
        
        # Validate stock settings
        if data.get('track_inventory', True) and data.get('stock_quantity', 0) == 0:
            if data.get('available', True):
                raise serializers.ValidationError({
                    'stock_quantity': 'Product cannot be available with zero stock when tracking inventory.'
                })
        
        return data
    
    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Regenerate slug if name changes
        if 'name' in validated_data and validated_data['name'] != instance.name:
            instance.slug = slugify(validated_data['name'])
        
        return super().update(instance, validated_data)

class StockUpdateSerializer(serializers.Serializer):
    """Serializer for updating product stock."""
    action = serializers.ChoiceField(choices=['increase', 'decrease', 'set'])
    quantity = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=255, required=False)
    
    def validate_quantity(self, value):
        """Validate quantity based on action."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def validate(self, data):
        """Validate stock update data."""
        product = self.context.get('product')
        
        if not product:
            raise serializers.ValidationError("Product context is required.")
        
        if not product.track_inventory:
            raise serializers.ValidationError("This product does not track inventory.")
        
        # Validate decrease action
        if data['action'] == 'decrease':
            if product.stock_quantity < data['quantity']:
                raise serializers.ValidationError({
                    'quantity': f'Cannot decrease stock by {data["quantity"]}. '
                               f'Current stock is {product.stock_quantity}.'
                })
        
        return data


class ProductSearchSerializer(serializers.ModelSerializer):
    """Serializer for product search results."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'price', 'available',
            'category_name', 'is_in_stock', 'description'
        ]
    
    def get_is_in_stock(self, obj):
        """Check if product is in stock."""
        return obj.is_in_stock()


class ProductBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk product operations."""
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        'activate', 'deactivate', 'delete', 'update_category'
    ])
    category_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        """Validate bulk update data."""
        if data['action'] == 'update_category' and not data.get('category_id'):
            raise serializers.ValidationError({
                'category_id': 'Category ID is required for update_category action.'
            })
        
        # Validate that all product IDs exist
        existing_ids = Product.objects.filter(
            id__in=data['product_ids']
        ).values_list('id', flat=True)
        
        missing_ids = set(data['product_ids']) - set(existing_ids)
        if missing_ids:
            raise serializers.ValidationError({
                'product_ids': f'Products with IDs {list(missing_ids)} do not exist.'
            })
        
        return data