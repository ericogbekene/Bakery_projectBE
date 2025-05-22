from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Category, Product
from .serializers import (
    CategoryListSerializer, CategoryDetailSerializer, CategoryCreateUpdateSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    StockUpdateSerializer, ProductSearchSerializer, ProductBulkUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category model.
    Provides CRUD operations and additional functionality.
    """
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'meta_description', 'meta_keywords']
    ordering_fields = ['name', 'id']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategoryDetailSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned categories,
        by filtering against query parameters.
        """
        queryset = Category.objects.all()
        
        # Filter categories that have products
        has_products = self.request.query_params.get('has_products')
        if has_products:
            if has_products.lower() == 'true':
                queryset = queryset.filter(products__isnull=False).distinct()
            elif has_products.lower() == 'false':
                queryset = queryset.filter(products__isnull=True)
        
        return queryset

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get all products in this category with filtering options."""
        category = self.get_object()
        products = category.products.filter(available=True)
        
        # Apply filters
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        in_stock = request.query_params.get('in_stock')
        
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        if in_stock and in_stock.lower() == 'true':
            products = products.filter(
                Q(track_inventory=False, available=True) |
                Q(track_inventory=True, stock_quantity__gt=0, available=True)
            )
        
        # Pagination
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """Get category statistics."""
        category = self.get_object()
        products = category.products.all()
        
        stats = {
            'total_products': products.count(),
            'available_products': products.filter(available=True).count(),
            'unavailable_products': products.filter(available=False).count(),
            'in_stock_products': products.filter(
                Q(track_inventory=False, available=True) |
                Q(track_inventory=True, stock_quantity__gt=0, available=True)
            ).count(),
            'low_stock_products': products.filter(
                track_inventory=True,
                stock_quantity__lte=models.F('low_stock_threshold'),
                stock_quantity__gt=0
            ).count(),
            'out_of_stock_products': products.filter(
                track_inventory=True,
                stock_quantity=0
            ).count(),
            'average_price': products.aggregate(
                avg_price=models.Avg('price')
            )['avg_price'] or 0,
        }
        
        return Response(stats)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product model.
    Provides CRUD operations, stock management, and search functionality.
    """
    queryset = Product.objects.select_related('category').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'available', 'track_inventory']
    search_fields = ['name', 'description', 'meta_keywords']
    ordering_fields = ['name', 'price', 'created_at', 'stock_quantity']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'search':
            return ProductSearchSerializer
        elif self.action == 'update_stock':
            return StockUpdateSerializer
        elif self.action == 'bulk_update':
            return ProductBulkUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        """
        Filter products based on query parameters.
        """
        queryset = Product.objects.select_related('category').all()
        
        # Price range filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Stock filtering
        in_stock = self.request.query_params.get('in_stock')
        low_stock = self.request.query_params.get('low_stock')
        
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(
                Q(track_inventory=False, available=True) |
                Q(track_inventory=True, stock_quantity__gt=0, available=True)
            )
        elif in_stock and in_stock.lower() == 'false':
            queryset = queryset.filter(
                Q(track_inventory=True, stock_quantity=0) |
                Q(available=False)
            )
        
        if low_stock and low_stock.lower() == 'true':
            from django.db import models
            queryset = queryset.filter(
                track_inventory=True,
                stock_quantity__lte=models.F('low_stock_threshold'),
                stock_quantity__gt=0
            )
        
        # Category filtering by slug
        category_slug = self.request.query_params.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search functionality.
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({'detail': 'Search query parameter "q" is required.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Search in multiple fields
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(meta_keywords__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category').filter(available=True)
        
        # Apply additional filters
        category_slug = request.query_params.get('category_slug')
        if category_slug:
            products = products.filter(category__slug=category_slug)
        
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Pagination
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductSearchSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductSearchSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_stock(self, request, slug=None):
        """
        Update product stock levels.
        """
        product = self.get_object()
        serializer = StockUpdateSerializer(
            data=request.data, 
            context={'product': product, 'request': request}
        )
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            quantity = serializer.validated_data['quantity']
            reason = serializer.validated_data.get('reason', '')
            
            try:
                with transaction.atomic():
                    if action == 'increase':
                        product.increase_stock(quantity)
                        message = f'Increased stock by {quantity}'
                    elif action == 'decrease':
                        success = product.reduce_stock(quantity)
                        if not success:
                            return Response(
                                {'detail': 'Insufficient stock for this operation.'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        message = f'Decreased stock by {quantity}'
                    elif action == 'set':
                        product.stock_quantity = quantity
                        product.save()
                        message = f'Set stock to {quantity}'
                return Response({
                    'detail': message,
                    'current_stock': product.stock_quantity,
                    'is_in_stock': product.is_in_stock(),
                    'is_low_stock': product.is_low_stock()
                })
            
            except Exception as e:
                return Response(
                    {'detail': f'Error updating stock: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_update(self, request):
        """
        Bulk update multiple products.
        """
        serializer = ProductBulkUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            product_ids = serializer.validated_data['product_ids']
            action = serializer.validated_data['action']
            category_id = serializer.validated_data.get('category_id')
            
            try:
                with transaction.atomic():
                    products = Product.objects.filter(id__in=product_ids)
                    
                    if action == 'activate':
                        products.update(available=True)
                        message = f'Activated {products.count()} products'
                    elif action == 'deactivate':
                        products.update(available=False)
                        message = f'Deactivated {products.count()} products'
                    elif action == 'delete':
                        count = products.count()
                        products.delete()
                        message = f'Deleted {count} products'
                    elif action == 'update_category':
                        category = get_object_or_404(Category, id=category_id)
                        products.update(category=category)
                        message = f'Updated category for {products.count()} products'
                    
                return Response({'detail': message})
            
            except Exception as e:
                return Response(
                    {'detail': f'Error performing bulk update: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get products with low stock levels.
        """
        from django.db import models
        products = Product.objects.filter(
            track_inventory=True,
            stock_quantity__lte=models.F('low_stock_threshold'),
            stock_quantity__gt=0
        ).select_related('category')
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """
        Get out of stock products.
        """
        products = Product.objects.filter(
            track_inventory=True,
            stock_quantity=0
        ).select_related('category')
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products (you can customize this logic).
        For now, returns newest products.
        """
        products = Product.objects.filter(available=True).select_related('category')[:10]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """
        Get related products from the same category.
        """
        product = self.get_object()
        if not product.category:
            return Response([])
        
        related_products = Product.objects.filter(
            category=product.category,
            available=True
        ).exclude(id=product.id).select_related('category')[:6]
        
        serializer = ProductListSerializer(related_products, many=True, context={'request': request})
        return Response(serializer.data)