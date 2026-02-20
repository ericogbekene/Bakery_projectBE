from django.urls import path
from . import views

app_name = 'delivery-api'

urlpatterns = [
    # Public endpoints
    path('zones/', views.DeliveryZoneListView.as_view(), name='zone-list'),
    path('zones/<int:id>/', views.DeliveryZoneDetailView.as_view(), name='zone-detail'),
    path('calculate/', views.CalculateDeliveryFeeView.as_view(), name='calculate-fee'),
    path('available-dates/', views.AvailableDeliveryDatesView.as_view(), name='available-dates'),
    path('validate-address/', views.ValidateDeliveryAddressView.as_view(), name='validate-address'),
    
    # Admin endpoints
    path('admin/zones/', views.AdminDeliveryZoneListView.as_view(), name='admin-zone-list'),
    path('admin/zones/<int:id>/', views.AdminDeliveryZoneDetailView.as_view(), name='admin-zone-detail'),
    path('admin/pricing-rules/', views.AdminPricingRuleListView.as_view(), name='admin-pricing-list'),
    path('admin/pricing-rules/<int:id>/', views.AdminPricingRuleDetailView.as_view(), name='admin-pricing-detail'),
    path('admin/schedules/', views.AdminScheduleListView.as_view(), name='admin-schedule-list'),
    path('admin/schedules/<int:id>/', views.AdminScheduleDetailView.as_view(), name='admin-schedule-detail'),
    path('admin/exceptions/', views.AdminExceptionListView.as_view(), name='admin-exception-list'),
    path('admin/exceptions/<int:id>/', views.AdminExceptionDetailView.as_view(), name='admin-exception-detail'),
    path('admin/stats/', views.AdminZoneStatsView.as_view(), name='admin-stats'),
]