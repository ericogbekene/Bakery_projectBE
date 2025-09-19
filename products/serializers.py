from rest_framework import serializers
from .models import Category, Product
from django.utils.text import slugify


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Serializes a Category for list views, providing a count of available products.
    """
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count']
        read_only_fields = ['slug']

    def get_product_count(self, obj):
        """Returns the number of available products in the category."""
        return obj.products.filter(available=True).count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single Category for detail views, including a list of its products.
    """
    products = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count', 'products']
        read_only_fields = ['slug']

    def get_products(self, obj):
        """Returns a limited list of available products in the category."""
        products = obj.products.filter(available=True)[:10]  # Limit to 10 products for preview
        return ProductListSerializer(products, many=True, context=self.context).data

    def get_product_count(self, obj):
        """Returns the total number of available products in the category."""
        return obj.products.filter(available=True).count()


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializes a Category for create and update operations.
    """
    class Meta:
        model = Category
        fields = ['name', 'slug']

    def create(self, validated_data):
        """The slug is auto-generated in the model's save method.""" 
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Regenerates the slug if the category name changes."""
        if 'name' in validated_data and validated_data['name'] != instance.name:
            instance.slug = slugify(validated_data['name'])
        return super().update(instance, validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializes a Product for list views with essential fields.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
     # Include computed image URLs
    image_url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()
    medium_image_url = serializers.ReadOnlyField()
    large_image_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'price', 'available',
            'category_name', 'stock_quantity', 'is_in_stock', 'is_low_stock',
            'created_at'
        ]
        read_only_fields = ['slug', 'created_at', 'is_in_stock', 'is_low_stock']

    def get_is_in_stock(self, obj):
        """Checks if the product is currently in stock."""
        return obj.is_in_stock()

    def get_is_low_stock(self, obj):
        """Checks if the product stock is below the configured threshold."""
        return obj.is_low_stock()


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single Product for detail views with all fields.
    """
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
        """Checks if the product is currently in stock."""
        return obj.is_in_stock()

    def get_is_low_stock(self, obj):
        """Checks if the product stock is below the configured threshold."""
        return obj.is_low_stock()


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializes a Product for create and update operations.
    """
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=True)

    class Meta:
        model = Product
        fields = [
            'name', 'category', 'image', 'description', 'price', 'available',
            'stock_quantity', 'low_stock_threshold', 'track_inventory'
        ]

    def validate(self, data):
        """
        Provides cross-field validation for product data.
        """
        # Validate stock settings: A product cannot be available if it has zero stock
        # and inventory is being tracked.
        if data.get('track_inventory', True) and data.get('stock_quantity', 0) == 0:
            if data.get('available', True):
                raise serializers.ValidationError({
                    'stock_quantity': 'Product cannot be available with zero stock when tracking inventory.'
                })

        return data

    def update(self, instance, validated_data):
        """Regenerates the slug if the product name changes."""
        if 'name' in validated_data and validated_data['name'] != instance.name:
            instance.slug = slugify(validated_data['name'])

        return super().update(instance, validated_data)


class StockUpdateSerializer(serializers.Serializer):
    """
    Serializes data for updating a product's stock level.
    """
    action = serializers.ChoiceField(choices=['increase', 'decrease', 'set'])
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False)

    def validate(self, data):
        """
        Validates the stock update data against the product's current state.
        """
        product = self.context.get('product')

        if not product:
            raise serializers.ValidationError("Product context is required for validation.")

        if not product.track_inventory:
            raise serializers.ValidationError("This product does not track inventory.")

        # Ensure there is enough stock for a decrease operation
        if data['action'] == 'decrease' and product.stock_quantity < data['quantity']:
            raise serializers.ValidationError({
                'quantity': f'Cannot decrease stock by {data["quantity"]}. '
                           f'Current stock is {product.stock_quantity}.'
            })

        return data


class ProductSearchSerializer(serializers.ModelSerializer):
    """
    Serializes a Product for search results, providing key information.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'image', 'price', 'available',
            'category_name', 'is_in_stock', 'description'
        ]

    def get_is_in_stock(self, obj):
        """Checks if the product is currently in stock."""
        return obj.is_in_stock()


class ProductBulkUpdateSerializer(serializers.Serializer):
    """
    Serializes data for performing bulk operations on multiple products.
    """
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        'activate', 'deactivate', 'delete', 'update_category'
    ])
    category_id = serializers.IntegerField(required=False)

    def validate(self, data):
        """
        Validates the data for the bulk update operation.
        """
        # Category ID is required when the action is to update the category
        if data['action'] == 'update_category' and not data.get('category_id'):
            raise serializers.ValidationError({
                'category_id': 'Category ID is required for the update_category action.'
            })

        # Ensure all specified product IDs exist
        existing_ids = Product.objects.filter(
            id__in=data['product_ids']
        ).values_list('id', flat=True)

        missing_ids = set(data['product_ids']) - set(existing_ids)
        if missing_ids:
            raise serializers.ValidationError({
                'product_ids': f'Products with the following IDs do not exist: {list(missing_ids)}.'
            })

        return data