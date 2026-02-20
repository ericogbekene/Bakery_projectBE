from rest_framework import generics, filters, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from products.models import Product, Category
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductCakeDetailSerializer,
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryCreateUpdateSerializer,
    ProductTypeFilterSerializer,
    ProductSearchSerializer,
)
from .pagination import (
    StandardResultsSetPagination, 
    SmallResultsSetPagination,
    LargeResultsSetPagination
)


# ============================================================================
# CUSTOM PERMISSIONS
# ============================================================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit.
    Read-only for everyone else.
    """
    def has_permission(self, request, view):
        # Allow read-only for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for admin users
        return request.user and request.user.is_staff


class IsAdminForWrite(permissions.BasePermission):
    """
    Custom permission that allows:
    - Admin users: all operations
    - Authenticated users: read-only
    - Anonymous users: read-only
    """
    def has_permission(self, request, view):
        # Allow read-only for all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write operations require admin
        return request.user and request.user.is_staff


# ============================================================================
# PUBLIC VIEWS (No authentication required)
# ============================================================================

class ProductListView(generics.ListAPIView):
    """
    GET /api/products/
    
    List all available products with optional filtering.
    
    Query Parameters:
    - product_type: 'cake' or 'pastry'
    - category: category ID
    - available: true/false (default: true)
    - search: search in name and description
    """
    permission_classes = [permissions.AllowAny]  # Public access
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product_type', 'category', 'available']
    search_fields = ['name', 'description']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Return available products ordered by name.
        """
        return Product.objects.filter(available=True).order_by('name')
    
    def list(self, request, *args, **kwargs):
        """
        Override list to add filter information to response.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Validate filter parameters
        filter_serializer = ProductTypeFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=False)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'products': serializer.data,
                'filters': request.query_params,
                'total_count': queryset.count()
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'products': serializer.data,
            'filters': request.query_params,
            'total_count': queryset.count()
        })


class ProductCakeListView(generics.ListAPIView):
    """
    GET /api/products/cakes/
    
    List all available cakes only.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Return available cakes ordered by name.
        """
        return Product.objects.filter(
            product_type='cake', 
            available=True
        ).order_by('name')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'cakes': serializer.data,
                'count': queryset.count()
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'cakes': serializer.data,
            'count': queryset.count()
        })


class ProductPastryListView(generics.ListAPIView):
    """
    GET /api/products/pastries/
    
    List all available pastries only.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Return available pastries ordered by name.
        """
        return Product.objects.filter(
            product_type='pastry', 
            available=True
        ).order_by('name')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'pastries': serializer.data,
                'count': queryset.count()
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'pastries': serializer.data,
            'count': queryset.count()
        })


class ProductDetailView(generics.RetrieveAPIView):
    """
    GET /api/products/<slug:slug>/
    
    Get detailed information about a specific product.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'


class ProductCakeDetailView(APIView):
    """
    GET /api/products/<slug:slug>/customize/
    
    Get cake details with all available customization options.
    Only works for cakes, returns 400 for pastries.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    
    def get(self, request, slug):
        """
        Retrieve cake with customization options.
        """
        # Get the product
        product = get_object_or_404(
            Product.objects.filter(available=True),
            slug=slug
        )
        
        # Verify it's a cake
        if not product.is_cake:
            return Response(
                {'error': 'This endpoint is only for cakes.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Serialize with cake detail serializer
        serializer = ProductCakeDetailSerializer(
            product, 
            context={'request': request}
        )
        
        # Get customization options from cart app
        customization_options = self._get_customization_options()
        
        data = serializer.data
        data['customization_options'] = customization_options
        
        return Response(data)
    
    def _get_customization_options(self):
        """
        Helper method to get customization options.
        """
        from cart.models import (
            CakeSizeMultiplier, 
            CakeFlavorPrice, 
            CakeCustomizationOption
        )
        
        # Get active sizes
        sizes = CakeSizeMultiplier.objects.all().order_by('size')
        
        # Get active flavors
        flavors = CakeFlavorPrice.objects.filter(is_active=True)
        
        # Get active addons
        addons = CakeCustomizationOption.objects.filter(is_active=True)
        
        return {
            'sizes': [
                {
                    'id': size.id,
                    'size': size.size,
                    'display': size.get_size_display(),
                    'multiplier': str(size.multiplier)
                } for size in sizes
            ],
            'flavors': [
                {
                    'id': flavor.id,
                    'name': flavor.flavor,
                    'multiplier': str(flavor.price_multiplier)
                } for flavor in flavors
            ],
            'addons': [
                {
                    'id': addon.id,
                    'type': addon.customization_type,
                    'name': addon.get_customization_type_display(),
                    'price': str(addon.price_per_unit),
                    'description': addon.description
                } for addon in addons
            ]
        }


class CategoryListView(generics.ListAPIView):
    """
    GET /api/categories/
    
    List all categories with product counts.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategoryListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    pagination_class = SmallResultsSetPagination


class CategoryDetailView(generics.RetrieveAPIView):
    """
    GET /api/categories/<slug:slug>/
    
    Get category details with its products.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    lookup_field = 'slug'


class ProductSearchView(generics.ListAPIView):
    """
    GET /api/products/search/?q=<query>
    
    Search products by name or description.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    serializer_class = ProductSearchSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Return available products ordered by relevance.
        """
        return Product.objects.filter(available=True).order_by('name')


class ProductCountByTypeView(APIView):
    """
    GET /api/products/counts/
    
    Get counts of products by type.
    """
    permission_classes = [permissions.AllowAny]  # Public access
    
    def get(self, request):
        """
        Return counts of cakes and pastries.
        """
        cake_count = Product.objects.filter(
            product_type='cake', 
            available=True
        ).count()
        
        pastry_count = Product.objects.filter(
            product_type='pastry', 
            available=True
        ).count()
        
        return Response({
            'cakes': cake_count,
            'pastries': pastry_count,
            'total': cake_count + pastry_count
        })


# ============================================================================
# ADMIN/STAFF ONLY VIEWS (Require admin authentication)
# ============================================================================

class ProductCreateView(generics.CreateAPIView):
    """
    POST /api/products/create/
    
    Create a new product.
    Requires admin authentication.
    """
    permission_classes = [permissions.IsAdminUser]  # Admin only
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    pagination_class = LargeResultsSetPagination
    
    def perform_create(self, serializer):
        """
        Set the slug from name.
        """
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'message': 'Product created successfully.',
                'product': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class ProductUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/products/<slug:slug>/update/
    
    Update an existing product.
    Requires admin authentication.
    """
    permission_classes = [permissions.IsAdminUser]  # Admin only
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    lookup_field = 'slug'
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(
            {
                'message': 'Product updated successfully.',
                'product': serializer.data
            }
        )


class ProductDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/products/<slug:slug>/delete/
    
    Delete a product.
    Requires admin authentication.
    """
    permission_classes = [permissions.IsAdminUser]  # Admin only
    queryset = Product.objects.all()
    lookup_field = 'slug'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product_name = instance.name
        self.perform_destroy(instance)
        return Response(
            {'message': f'Product "{product_name}" deleted successfully.'},
            status=status.HTTP_200_OK
        )


class CategoryCreateView(generics.CreateAPIView):
    """
    POST /api/categories/create/
    
    Create a new category.
    Requires admin authentication.
    """
    permission_classes = [permissions.IsAdminUser]  # Admin only
    queryset = Category.objects.all()
    serializer_class = CategoryCreateUpdateSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'message': 'Category created successfully.',
                'category': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class CategoryUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/categories/<slug:slug>/update/
    
    Update an existing category.
    Requires admin authentication.
    """
    permission_classes = [permissions.IsAdminUser]  # Admin only
    queryset = Category.objects.all()
    serializer_class = CategoryCreateUpdateSerializer
    lookup_field = 'slug'
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(
            {
                'message': 'Category updated successfully.',
                'category': serializer.data
            }
        )


class CategoryDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/categories/<slug:slug>/delete/
    
    Delete a category.
    Requires admin authentication.
    """
    permission_classes = [permissions.IsAdminUser]  # Admin only
    queryset = Category.objects.all()
    lookup_field = 'slug'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        category_name = instance.name
        
        # Check if category has products
        if instance.products.exists():
            return Response(
                {
                    'error': 'Cannot delete category with existing products.',
                    'product_count': instance.products.count()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(
            {'message': f'Category "{category_name}" deleted successfully.'},
            status=status.HTTP_200_OK
        )