from django.urls import path
from .views import OrderView, OrderDetailView

urlpatterns = [
    path('create/', OrderView.as_view(), name='create_order'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),  # View order summary
]
