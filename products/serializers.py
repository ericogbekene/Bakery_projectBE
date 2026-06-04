from rest_framework import serializers
from django.utils.text import slugify
from products.models import Category, Product


class CategoryListSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    image_url = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image_url', 'product_count']
        read_only_fields = ['slug']

    def get_product_count(self, obj):
        return obj.products.filter(available=True).count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    image_url = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image_url', 'product_count', 'products']
        read_only_fields = ['slug']

    def get_products(self, obj):
        products = obj.products.filter(available=True)[:10]
        return ProductListSerializer(products, many=True, context=self.context).data

    def get_product_count(self, obj):
        return obj.products.filter(available=True).count()


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'image']

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'name' in validated_data and validated_data['name'] != instance.name:
            instance.slug = slugify(validated_data['name'])
        return super().update(instance, validated_data)
    

class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializes a Product for list views with essential fields.
    Updated for simplified product model with cake/pastry differentiation.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    # Image URLs
    image_url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()
    medium_image_url = serializers.ReadOnlyField()
    large_image_url = serializers.ReadOnlyField()
    
    # Display helpers
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'product_type', 'product_type_display',
            'image_url', 'thumbnail_url', 'medium_image_url', 'large_image_url',
            'price', 'available', 'category_name', 'created_at',
            # Cake-specific fields (will be null for pastries)
            'layers', 'covering', 'preparation_days'
        ]
        read_only_fields = [
            'slug', 'created_at', 'image_url', 'thumbnail_url',
            'medium_image_url', 'large_image_url', 'product_type_display'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializes a single Product for detail views with all fields.
    Updated for simplified product model.
    """
    category = CategoryListSerializer(read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    
    # Image URLs
    image_url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()
    medium_image_url = serializers.ReadOnlyField()
    large_image_url = serializers.ReadOnlyField()
    
    # Helper properties - FIXED: removed redundant source arguments
    is_cake = serializers.BooleanField(read_only=True)
    is_pastry = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'product_type', 'product_type_display',
            'image_url', 'thumbnail_url', 'medium_image_url', 'large_image_url',
            'description', 'price', 'available', 'category', 'created_at', 'updated_at',
            'is_cake', 'is_pastry',
            # Cake-specific fields
            'layers', 'covering', 'inspiration', 'preparation_days'
        ]
        read_only_fields = [
            'slug', 'created_at', 'updated_at', 'image_url', 'thumbnail_url',
            'medium_image_url', 'large_image_url', 'is_cake', 'is_pastry'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializes a Product for create and update operations.
    Includes conditional validation based on product_type.
    """
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'name', 'product_type', 'category', 'image', 'description', 
            'price', 'available',
            # Cake-specific fields
            'layers', 'covering', 'inspiration', 'preparation_days'
        ]

    def validate(self, data):
        """
        Conditional validation based on product_type.
        - For cakes: layers, covering, preparation_days are required
        - For pastries: cake fields should be empty/null
        """
        product_type = data.get('product_type')
        
        # If updating, get existing product_type if not provided
        if not product_type and self.instance:
            product_type = self.instance.product_type
        
        # Validation for cakes
        if product_type == 'cake':
            errors = {}
            
            # Required fields for cakes
            if not data.get('layers') and not (self.instance and self.instance.layers):
                errors['layers'] = 'Layers is required for cakes.'
            
            if not data.get('covering') and not (self.instance and self.instance.covering):
                errors['covering'] = 'Covering type is required for cakes.'
            
            if not data.get('preparation_days') and not (self.instance and self.instance.preparation_days):
                errors['preparation_days'] = 'Preparation days is required for cakes.'
            
            # Validate values
            if data.get('layers') and data['layers'] < 1:
                errors['layers'] = 'Cake must have at least 1 layer.'
            
            if data.get('preparation_days') and data['preparation_days'] < 1:
                errors['preparation_days'] = 'Preparation days must be at least 1.'
            
            if errors:
                raise serializers.ValidationError(errors)
        
        # Validation for pastries
        elif product_type == 'pastry':
            errors = {}
            
            # Cake fields should be empty for pastries
            if data.get('layers'):
                errors['layers'] = 'Layers field should not be set for pastries.'
            
            if data.get('covering'):
                errors['covering'] = 'Covering field should not be set for pastries.'
            
            if data.get('inspiration'):
                errors['inspiration'] = 'Inspiration field should not be set for pastries.'
            
            if data.get('preparation_days'):
                errors['preparation_days'] = 'Preparation days should not be set for pastries.'
            
            if errors:
                raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """Create a new product."""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Regenerates the slug if the product name changes."""
        if 'name' in validated_data and validated_data['name'] != instance.name:
            instance.slug = slugify(validated_data['name'])
        
        return super().update(instance, validated_data)


class ProductCakeDetailSerializer(serializers.ModelSerializer):
    """
    Specialized serializer for cakes that includes all customization options.
    Used for the cake detail page where customers customize.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.ReadOnlyField()
    medium_image_url = serializers.ReadOnlyField()
    large_image_url = serializers.ReadOnlyField()
    
    # Helper properties
    is_cake = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'image_url',
            'medium_image_url', 'large_image_url', 'category_name',
            'layers', 'covering', 'inspiration', 'preparation_days',
            'is_cake'
        ]


class ProductSearchSerializer(serializers.ModelSerializer):
    """
    Serializes a Product for search results, providing key information.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    image_url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'product_type', 'product_type_display',
            'image_url', 'thumbnail_url', 'price', 'available',
            'category_name', 'description'
        ]


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
    category_id = serializers.IntegerField(required=False, allow_null=True)

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


class ProductTypeFilterSerializer(serializers.Serializer):
    """
    Serializer for filtering products by type.
    """
    product_type = serializers.ChoiceField(
        choices=Product.PRODUCT_TYPES,
        required=False,
        help_text="Filter by product type: cake or pastry"
    )
    category = serializers.IntegerField(
        required=False,
        help_text="Filter by category ID"
    )
    available = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Filter by availability"
    )
    search = serializers.CharField(
        required=False,
        help_text="Search in name and description"
    )