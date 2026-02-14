# from rest_framework import viewsets, status, filters
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend
# from django.db.models import Q, Count, Avg, F
# from django.shortcuts import get_object_or_404
# from django.db import transaction

# from .models import Category, Product
# from .serializers import (
#     CategoryListSerializer, CategoryDetailSerializer, CategoryCreateUpdateSerializer,
#     ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
#     StockUpdateSerializer, ProductSearchSerializer, ProductBulkUpdateSerializer
# )


# class CategoryViewSet(viewsets.ModelViewSet):
#     """
#     Provides a comprehensive API for managing product categories.

#     This ViewSet supports:
#     - Listing all categories.
#     - Retrieving a single category by its slug.
#     - Creating, updating, and deleting categories.
#     - Filtering categories based on whether they contain products.
#     - Retrieving all products within a specific category.
#     - Getting statistics for a category.
#     """
#     queryset = Category.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     lookup_field = 'slug'
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ['name']
#     ordering_fields = ['name', 'id']
#     ordering = ['name']

#     def get_serializer_class(self):
#         """
#         Dynamically selects the appropriate serializer based on the request action.
#         """
#         if self.action == 'list':
#             return CategoryListSerializer
#         elif self.action in ['create', 'update', 'partial_update']:
#             return CategoryCreateUpdateSerializer
#         return CategoryDetailSerializer

#     def get_queryset(self):
#         """
#         Optionally filters the queryset to return categories based on whether they have products.

#         Query Parameters:
#         - `has_products` (boolean): If `true`, returns categories with at least one product.
#                                   If `false`, returns categories with no products.
#         """
#         queryset = super().get_queryset()

#         has_products = self.request.query_params.get('has_products')
#         if has_products is not None:
#             if has_products.lower() == 'true':
#                 queryset = queryset.filter(products__isnull=False).distinct()
#             elif has_products.lower() == 'false':
#                 queryset = queryset.filter(products__isnull=True)

#         return queryset

#     @action(detail=True, methods=['get'])
#     def products(self, request, slug=None):
#         """
#         Retrieves all available products within a specific category, with optional filtering.

#         Query Parameters:
#         - `min_price` (decimal): Filters products with a price greater than or equal to this value.
#         - `max_price` (decimal): Filters products with a price less than or equal to this value.
#         - `in_stock` (boolean): If `true`, returns only products that are in stock.
#         """
#         category = self.get_object()
#         products = category.products.filter(available=True)

#         # Apply optional filters from query parameters
#         min_price = request.query_params.get('min_price')
#         if min_price:
#             products = products.filter(price__gte=min_price)

#         max_price = request.query_params.get('max_price')
#         if max_price:
#             products = products.filter(price__lte=max_price)

#         in_stock = request.query_params.get('in_stock')
#         if in_stock and in_stock.lower() == 'true':
#             products = products.filter(
#                 Q(track_inventory=False, available=True) |
#                 Q(track_inventory=True, stock_quantity__gt=0, available=True)
#             )

#         # Paginate the results
#         page = self.paginate_queryset(products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True, context={'request': request})
#             return self.get_paginated_response(serializer.data)

#         serializer = ProductListSerializer(products, many=True, context={'request': request})
#         return Response(serializer.data)

#     @action(detail=True, methods=['get'])
#     def stats(self, request, slug=None):
#         """
#         Provides statistics for a specific category, such as product counts and average price.
#         """
#         category = self.get_object()
#         products = category.products.all()

#         stats = {
#             'total_products': products.count(),
#             'available_products': products.filter(available=True).count(),
#             'unavailable_products': products.filter(available=False).count(),
#             'in_stock_products': products.filter(
#                 Q(track_inventory=False, available=True) |
#                 Q(track_inventory=True, stock_quantity__gt=0, available=True)
#             ).count(),
#             'low_stock_products': products.filter(
#                 track_inventory=True,
#                 stock_quantity__lte=F('low_stock_threshold'),
#                 stock_quantity__gt=0
#             ).count(),
#             'out_of_stock_products': products.filter(
#                 track_inventory=True,
#                 stock_quantity=0
#             ).count(),
#             'average_price': products.aggregate(avg_price=Avg('price'))['avg_price'] or 0,
#         }

#         return Response(stats)


# class ProductViewSet(viewsets.ModelViewSet):
#     """
#     Provides a comprehensive API for managing products.

#     This ViewSet supports:
#     - Listing, retrieving, creating, updating, and deleting products.
#     - Advanced filtering by category, price, and stock status.
#     - Full-text search across product name and description.
#     - Specialized actions for stock management and bulk updates.
#     """
#     queryset = Product.objects.select_related('category').all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     lookup_field = 'slug'
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['category', 'available', 'track_inventory']
#     search_fields = ['name', 'description']
#     ordering_fields = ['name', 'price', 'created_at', 'stock_quantity']
#     ordering = ['-created_at']

#     def get_serializer_class(self):
#         """
#         Dynamically selects the appropriate serializer based on the request action.
#         """
#         if self.action == 'list':
#             return ProductListSerializer
#         elif self.action in ['create', 'update', 'partial_update']:
#             return ProductCreateUpdateSerializer
#         elif self.action == 'search':
#             return ProductSearchSerializer
#         elif self.action == 'update_stock':
#             return StockUpdateSerializer
#         elif self.action == 'bulk_update':
#             return ProductBulkUpdateSerializer
#         return ProductDetailSerializer

#     def get_queryset(self):
#         """
#         Extends the default queryset to allow for advanced filtering based on query parameters.

#         Query Parameters:
#         - `min_price` (decimal): Filters for price greater than or equal to this value.
#         - `max_price` (decimal): Filters for price less than or equal to this value.
#         - `in_stock` (boolean): Filters for products that are in stock.
#         - `low_stock` (boolean): Filters for products with low stock levels.
#         - `category_slug` (string): Filters products by their category slug.
#         """
#         queryset = super().get_queryset()

#         # Price range filtering
#         min_price = self.request.query_params.get('min_price')
#         if min_price:
#             queryset = queryset.filter(price__gte=min_price)

#         max_price = self.request.query_params.get('max_price')
#         if max_price:
#             queryset = queryset.filter(price__lte=max_price)

#         # Stock-based filtering
#         in_stock = self.request.query_params.get('in_stock')
#         if in_stock is not None:
#             if in_stock.lower() == 'true':
#                 queryset = queryset.filter(
#                     Q(track_inventory=False, available=True) |
#                     Q(track_inventory=True, stock_quantity__gt=0, available=True)
#                 )
#             elif in_stock.lower() == 'false':
#                 queryset = queryset.filter(
#                     Q(track_inventory=True, stock_quantity=0) |
#                     Q(available=False)
#                 )

#         low_stock = self.request.query_params.get('low_stock')
#         if low_stock and low_stock.lower() == 'true':
#             queryset = queryset.filter(
#                 track_inventory=True,
#                 stock_quantity__lte=F('low_stock_threshold'),
#                 stock_quantity__gt=0
#             )

#         # Category filtering
#         category_slug = self.request.query_params.get('category_slug')
#         if category_slug:
#             queryset = queryset.filter(category__slug=category_slug)

#         return queryset

#     @action(detail=False, methods=['get'])
#     def search(self, request):
#         """
#         Provides full-text search functionality across multiple product fields.

#         Query Parameters:
#         - `q` (string): The search query.
#         - `category_slug` (string): An optional category to scope the search.
#         - `min_price`, `max_price` (decimal): Optional price range filters.
#         """
#         query = request.query_params.get('q', '')
#         if not query:
#             return Response({'detail': 'Search query parameter "q" is required.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Search across name, description, and category name
#         products = Product.objects.filter(
#             Q(name__icontains=query) |
#             Q(description__icontains=query) |
#             Q(category__name__icontains=query)
#         ).select_related('category').filter(available=True)

#         # Apply additional filters
#         category_slug = request.query_params.get('category_slug')
#         if category_slug:
#             products = products.filter(category__slug=category_slug)

#         min_price = request.query_params.get('min_price')
#         if min_price:
#             products = products.filter(price__gte=min_price)

#         max_price = request.query_params.get('max_price')
#         if max_price:
#             products = products.filter(price__lte=max_price)

#         # Paginate the results
#         page = self.paginate_queryset(products)
#         if page is not None:
#             serializer = ProductSearchSerializer(page, many=True, context={'request': request})
#             return self.get_paginated_response(serializer.data)

#         serializer = ProductSearchSerializer(products, many=True, context={'request': request})
#         return Response(serializer.data)

#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def update_stock(self, request, slug=None):
#         """
#         Updates the stock level of a single product.
#         Requires authentication.

#         Request Body:
#         - `action` (string): 'increase', 'decrease', or 'set'.
#         - `quantity` (integer): The amount to adjust the stock by.
#         - `reason` (string, optional): A reason for the stock adjustment.
#         """
#         product = self.get_object()
#         serializer = StockUpdateSerializer(data=request.data, context={'product': product, 'request': request})

#         if serializer.is_valid():
#             action = serializer.validated_data['action']
#             quantity = serializer.validated_data['quantity']

#             try:
#                 with transaction.atomic():
#                     if action == 'increase':
#                         product.increase_stock(quantity)
#                         message = f'Increased stock by {quantity}'
#                     elif action == 'decrease':
#                         if not product.reduce_stock(quantity):
#                             return Response({'detail': 'Insufficient stock for this operation.'}, status=status.HTTP_400_BAD_REQUEST)
#                         message = f'Decreased stock by {quantity}'
#                     elif action == 'set':
#                         product.stock_quantity = quantity
#                         product.save()
#                         message = f'Set stock to {quantity}'

#                 return Response({
#                     'detail': message,
#                     'current_stock': product.stock_quantity,
#                     'is_in_stock': product.is_in_stock(),
#                     'is_low_stock': product.is_low_stock()
#                 })

#             except Exception as e:
#                 return Response({'detail': f'Error updating stock: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
#     def bulk_update(self, request):
#         """
#         Performs bulk actions on a list of products.
#         Requires authentication.

#         Request Body:
#         - `product_ids` (list of integers): The IDs of the products to update.
#         - `action` (string): 'activate', 'deactivate', 'delete', or 'update_category'.
#         - `category_id` (integer, optional): Required if action is 'update_category'.
#         """
#         serializer = ProductBulkUpdateSerializer(data=request.data)

#         if serializer.is_valid():
#             product_ids = serializer.validated_data['product_ids']
#             action = serializer.validated_data['action']

#             try:
#                 with transaction.atomic():
#                     products = Product.objects.filter(id__in=product_ids)

#                     if action == 'activate':
#                         products.update(available=True)
#                         message = f'Activated {products.count()} products'
#                     elif action == 'deactivate':
#                         products.update(available=False)
#                         message = f'Deactivated {products.count()} products'
#                     elif action == 'delete':
#                         count, _ = products.delete()
#                         message = f'Deleted {count} products'
#                     elif action == 'update_category':
#                         category_id = serializer.validated_data.get('category_id')
#                         category = get_object_or_404(Category, id=category_id)
#                         products.update(category=category)
#                         message = f'Updated category for {products.count()} products'

#                 return Response({'detail': message})

#             except Exception as e:
#                 return Response({'detail': f'Error performing bulk update: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['get'])
#     def low_stock(self, request):
#         """
#         Retrieves a list of products that are low on stock.
#         """
#         products = Product.objects.filter(
#             track_inventory=True,
#             stock_quantity__lte=F('low_stock_threshold'),
#             stock_quantity__gt=0
#         ).select_related('category')

#         page = self.paginate_queryset(products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True, context={'request': request})
#             return self.get_paginated_response(serializer.data)

#         serializer = ProductListSerializer(products, many=True, context={'request': request})
#         return Response(serializer.data)

#     @action(detail=False, methods=['get'])
#     def out_of_stock(self, request):
#         """
#         Retrieves a list of products that are out of stock.
#         """
#         products = Product.objects.filter(
#             track_inventory=True,
#             stock_quantity=0
#         ).select_related('category')

#         page = self.paginate_queryset(products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True, context={'request': request})
#             return self.get_paginated_response(serializer.data)

#         serializer = ProductListSerializer(products, many=True, context={'request': request})
#         return Response(serializer.data)

#     @action(detail=False, methods=['get'])
#     def featured(self, request):
#         """
#         Retrieves a list of featured products.
#         Currently, this returns the 10 newest available products.
#         """
#         products = Product.objects.filter(available=True).select_related('category')[:10]
#         serializer = ProductListSerializer(products, many=True, context={'request': request})
#         return Response(serializer.data)

#     @action(detail=True, methods=['get'])
#     def related(self, request, slug=None):
#         """
#         Retrieves a list of related products from the same category.
#         """
#         product = self.get_object()
#         if not product.category:
#             return Response([])

#         related_products = Product.objects.filter(
#             category=product.category,
#             available=True
#         ).exclude(id=product.id).select_related('category')[:6]

#         serializer = ProductListSerializer(related_products, many=True, context={'request': request})
#         return Response(serializer.data)