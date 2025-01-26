from django.urls import path
from .views import CartAddUpdateView, CartRemoveView, CartDetailView

urlpatterns = [
    path('add/', CartAddUpdateView.as_view(), name='cart_add_update'),
    path('remove/<int:product_id>/', CartRemoveView.as_view(), name='cart_remove'),
    path('cart-detail/', CartDetailView.as_view(), name='cart_detail'),
]
