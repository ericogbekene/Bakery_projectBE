from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
# router.register('users', UserViewSet, 'user')
router.register(r'products', views.ProductViewSet, basename='products')
router.register(r'categories', views.CategoryViewSet, basename='categories')
#router.register(r'orders', views.OrderViewSet, basename='orders')
#router.register(r'order-items', views.OrderItemViewSet, basename='order-items')
#router.register(r'carts', views.CartViewSet, basename='carts')
#router.register(r'cart-items', views.CartItemViewSet, basename='cart-items')



urlpatterns = [
    path('', include(router.urls))
    #path('products/', ProductViewSet.as_view(), name='products'),
    #path('jobs/', views.jobs, name='jobs')
]