from django.urls import path
from . import views

app_name = 'products-api'

urlpatterns = [
    # Public endpoints
    path('', views.ProductListView.as_view(), name='product-list'),
    path('cakes/', views.ProductCakeListView.as_view(), name='product-cake-list'),
    path('pastries/', views.ProductPastryListView.as_view(), name='product-pastry-list'),
    path('search/', views.ProductSearchView.as_view(), name='product-search'),
    path('counts/', views.ProductCountByTypeView.as_view(), name='product-counts'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<slug:slug>/customize/', views.ProductCakeDetailView.as_view(), name='product-cake-customize'),
    
    # Category endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Admin endpoints (should be protected with permissions)
    path('create/', views.ProductCreateView.as_view(), name='product-create'),
    path('<slug:slug>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    path('<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<slug:slug>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<slug:slug>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),
]