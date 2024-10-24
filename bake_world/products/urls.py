from django.urls import path, include
from . import views
from .views import ProductViewSet
from rest_framework import routers

router = routers.DefaultRouter()
# router.register('users', UserViewSet, 'user')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'categories', views.CategoryViewSet, basename='categories')



urlpatterns = [
    path('', include(router.urls))
    #path('products/', ProductViewSet.as_view(), name='products'),
    #path('jobs/', views.jobs, name='jobs')
]