from django.urls import path
from . import views

app_name = 'cart-api'

urlpatterns = [
    # Main cart endpoints
    path('', views.CartDetailView.as_view(), name='cart-detail'),
    path('add/', views.AddToCartView.as_view(), name='cart-add'),
    path('count/', views.CartItemCountView.as_view(), name='cart-count'),
    path('summary/', views.CartSummaryView.as_view(), name='cart-summary'),
    path('calculate-price/', views.CalculatePriceView.as_view(), name='calculate-price'),
    
    # Cart item endpoints
    path('items/<int:item_id>/', views.CartItemDetailView.as_view(), name='cart-item-detail'),
    
    # Delivery endpoints
    path('delivery/', views.DeliveryInfoView.as_view(), name='cart-delivery'),
    
    # Guest cart merging (for authenticated users)
    path('merge/', views.MergeGuestCartView.as_view(), name='cart-merge'),
]