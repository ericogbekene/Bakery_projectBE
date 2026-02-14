# from django.urls import path
# from . import views

# app_name = 'cart'

# urlpatterns = [
    
#     # ====================================================================
#     # PRICING & PRODUCT INFO ENDPOINTS
#     # ====================================================================
    
#     path('api/products/<int:product_id>/details/', 
#          views.ProductDetailAPIView.as_view(), 
#          name='product_detail_api'),
    
#     path('api/pricing/', 
#          views.PricingInfoAPIView.as_view(), 
#          name='pricing_info'),
    
#     path('api/calculate-cake-price/', 
#          views.CalculateCakePriceAPIView.as_view(), 
#          name='calculate_cake_price'),
    
    
#     # ====================================================================
#     # CART MANAGEMENT ENDPOINTS
#     # ====================================================================
    
#     path('api/cart/', 
#          views.CartDetailAPIView.as_view(), 
#          name='cart_detail_api'),
    
#     path('api/cart/add/', 
#          views.AddToCartAPIView.as_view(), 
#          name='add_to_cart_api'),
    
#     path('api/cart/item/<int:cart_item_id>/', 
#          views.UpdateCartItemAPIView.as_view(), 
#          name='update_cart_item_api'),
    
#     path('api/cart/item/<int:cart_item_id>/delete/', 
#          views.RemoveFromCartAPIView.as_view(), 
#          name='remove_from_cart_api'),
    
#     path('api/cart/clear/', 
#          views.ClearCartAPIView.as_view(), 
#          name='clear_cart_api'),
    
#     path('api/cart/count/', 
#          views.CartItemCountAPIView.as_view(), 
#          name='cart_count_api'),
    
#     path('api/cart/total/', 
#          views.CartTotalAPIView.as_view(), 
#          name='cart_total_api'),
# ]