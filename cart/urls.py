from django.urls import path
from .views import CartAddUpdateView, CartRemoveView, CartDetailView, CartClearView

urlpatterns = [
    path('cart/add/', CartAddUpdateView.as_view(), name='cart-add'),
    path('cart/remove/', CartRemoveView.as_view(), name='cart-remove'),
    path('cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),
]
