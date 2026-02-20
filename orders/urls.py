from django.urls import path
from . import views

app_name = 'orders-api'

urlpatterns = [
    # Public endpoints
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.CreateOrderView.as_view(), name='order-create'),
    path('<int:id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:id>/cancel/', views.CancelOrderView.as_view(), name='order-cancel'),
    path('<int:id>/track/', views.TrackOrderView.as_view(), name='order-track'),
    
    # Admin endpoints
    path('admin/<int:id>/update-status/', views.AdminOrderUpdateView.as_view(), name='order-update-status'),
    path('admin/<int:id>/update-payment/', views.AdminPaymentUpdateView.as_view(), name='order-update-payment'),
    path('admin/stats/', views.AdminOrderStatsView.as_view(), name='order-stats'),
]