from django.urls import path
from . import views
from .views import ProductViewSet

urlpatterns = [
    path('products/', ProductViewSet.as_view(), name='products'),
    path('jobs/', views.jobs, name='jobs')
]