from django.urls import path
from . import views

app_name = 'products-api'

urlpatterns = [
    # ----------------------------------------------------------------
    # Fixed paths MUST come before <slug:slug>/ wildcard patterns
    # otherwise Django matches 'categories', 'create', 'search', etc.
    # as product slugs and returns 404s
    # ----------------------------------------------------------------

    # Public endpoints — fixed paths first
    path('', views.ProductListView.as_view(), name='product-list'),
    path('cakes/', views.ProductCakeListView.as_view(), name='product-cake-list'),
    path('pastries/', views.ProductPastryListView.as_view(), name='product-pastry-list'),
    path('search/', views.ProductSearchView.as_view(), name='product-search'),
    path('counts/', views.ProductCountByTypeView.as_view(), name='product-counts'),

    # Category endpoints — fixed paths before wildcards
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:slug>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<slug:slug>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # Admin endpoints — fixed paths before wildcards
    path('create/', views.ProductCreateView.as_view(), name='product-create'),

    # Wildcard slug patterns LAST — these must come after all fixed paths
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<slug:slug>/customize/', views.ProductCakeDetailView.as_view(), name='product-cake-customize'),
    path('<slug:slug>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    path('<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
]