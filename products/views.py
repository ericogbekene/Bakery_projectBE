from rest_framework import generics, filters, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
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
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

class ProductListView(generics.ListAPIView):
    """
    GET /api/products/

    Supported query parameters:
      - search:          text search on name/description
      - product_type:    'cake' or 'pastry'
      - category:        category integer ID  (e.g. ?category=3)
      - category_slug:   category slug        (e.g. ?category_slug=signature-cakes)
      - page, page_size: pagination

    FIX 1: Removed the custom list() override that wrapped paginated results
            inside { products: [...] }. The standard DRF shape is returned:
            { count, next, previous, total_pages, current_page, page_size, results: [...] }

    FIX 2: Added category_slug filtering so the frontend can pass the slug
            directly from the URL without a separate ID lookup.

    FIX 3: Removed DjangoFilterBackend for category — it was rejecting slug
            strings with "Select a valid choice" because it expected an integer.
            Filtering is now done manually in get_queryset().

    FIX 4: Added select_related('category') to avoid N+1 queries.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = Product.objects.filter(
            available=True
        ).select_related('category').order_by('name')

        # Filter by product_type
        product_type = self.request.query_params.get('product_type')
        if product_type in ['cake', 'pastry']:
            queryset = queryset.filter(product_type=product_type)

        # Filter by category — accept ALL of these from the frontend:
        #   ?category=3                (integer ID)
        #   ?category=signature-cakes  (slug sent as ?category=)
        #   ?category_slug=signature-cakes (explicit slug param)
        category = self.request.query_params.get('category')
        category_slug = self.request.query_params.get('category_slug')

        if category:
            if category.isdigit():
                # It's a numeric ID
                queryset = queryset.filter(category_id=category)
            else:
                # It's a slug string (e.g. "signature-cakes")
                queryset = queryset.filter(category__slug=category)
        elif category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset


class ProductCakeListView(generics.ListAPIView):
    """
    GET /api/products/cakes/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Product.objects.filter(
            product_type='cake',
            available=True
        ).select_related('category').order_by('name')


class ProductPastryListView(generics.ListAPIView):
    """
    GET /api/products/pastries/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Product.objects.filter(
            product_type='pastry',
            available=True
        ).select_related('category').order_by('name')


class ProductDetailView(generics.RetrieveAPIView):
    """
    GET /api/products/<slug>/
    """
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(available=True).select_related('category')
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'


class ProductCakeDetailView(APIView):
    """
    GET /api/products/<slug>/customize/
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get Cake Customization Options",
        responses={
            200: openapi.Response(description="Cake details with customization options."),
            400: openapi.Response(description="This endpoint is only for cakes."),
            404: openapi.Response(description="Product not found."),
        }
    )
    def get(self, request, slug):
        product = get_object_or_404(Product.objects.filter(available=True), slug=slug)

        if not product.is_cake:
            return Response(
                {'error': 'This endpoint is only for cakes.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductCakeDetailSerializer(product, context={'request': request})
        data = serializer.data
        data['customization_options'] = self._get_customization_options()
        return Response(data)

    def _get_customization_options(self):
        from cart.models import CakeSizeMultiplier, CakeFlavorPrice, CakeCustomizationOption

        sizes  = CakeSizeMultiplier.objects.all().order_by('size')
        flavors = CakeFlavorPrice.objects.filter(is_active=True)
        addons  = CakeCustomizationOption.objects.filter(is_active=True)

        return {
            'sizes': [
                {
                    'id': s.id,
                    'size': s.size,
                    'display': s.get_size_display(),
                    'multiplier': str(s.multiplier)
                } for s in sizes
            ],
            'flavors': [
                {
                    'id': f.id,
                    'name': f.flavor,
                    'multiplier': str(f.price_multiplier)
                } for f in flavors
            ],
            'addons': [
                {
                    'id': a.id,
                    'type': a.customization_type,
                    'name': a.get_customization_type_display(),
                    'price': str(a.price_per_unit),
                    'description': a.description
                } for a in addons
            ]
        }


class CategoryListView(generics.ListAPIView):
    """
    GET /api/products/categories/
    """
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategoryListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    pagination_class = SmallResultsSetPagination


class CategoryDetailView(generics.RetrieveAPIView):
    """
    GET /api/products/categories/<slug>/
    """
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    lookup_field = 'slug'


class ProductSearchView(generics.ListAPIView):
    """
    GET /api/products/search/?search=<query>

    NOTE: use ?search= not ?q=
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSearchSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Product.objects.filter(
            available=True
        ).select_related('category').order_by('name')


class ProductCountByTypeView(APIView):
    """
    GET /api/products/counts/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cake_count   = Product.objects.filter(product_type='cake',   available=True).count()
        pastry_count = Product.objects.filter(product_type='pastry', available=True).count()
        return Response({
            'cakes':   cake_count,
            'pastries': pastry_count,
            'total':   cake_count + pastry_count
        })


# ============================================================================
# ADMIN VIEWS
# ============================================================================

class ProductCreateView(generics.CreateAPIView):
    """
    POST /api/products/create/
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'Product created successfully.', 'product': serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class ProductUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/products/<slug>/update/
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'message': 'Product updated successfully.', 'product': serializer.data})


class ProductDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/products/<slug>/delete/
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = 'slug'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({'message': f'Product "{name}" deleted successfully.'}, status=status.HTTP_200_OK)


class CategoryCreateView(generics.CreateAPIView):
    """
    POST /api/products/categories/create/
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategoryCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'message': 'Category created successfully.', 'category': serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class CategoryUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/products/categories/<slug>/update/
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategoryCreateUpdateSerializer
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'message': 'Category updated successfully.', 'category': serializer.data})


class CategoryDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/products/categories/<slug>/delete/
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Category.objects.all()
    lookup_field = 'slug'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        if instance.products.exists():
            return Response(
                {'error': 'Cannot delete category with existing products.', 'product_count': instance.products.count()},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response({'message': f'Category "{name}" deleted successfully.'}, status=status.HTTP_200_OK)