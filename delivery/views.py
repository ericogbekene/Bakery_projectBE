from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from delivery.models import (
    DeliveryZone, DeliverySchedule, DeliveryException, DeliveryService
)
from .serializers import (
    DeliveryZoneSerializer, DeliveryZoneListSerializer,
    DeliveryScheduleSerializer, DeliveryExceptionSerializer,
    CalculateDeliveryFeeSerializer, DeliveryFeeResponseSerializer,
    AvailableDatesSerializer, AvailableDateSerializer
)


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

class DeliveryZoneListView(generics.ListAPIView):
    """
    GET /api/delivery/zones/

    List all active delivery zones. Used by the frontend to populate
    the delivery area dropdown at checkout — only areas added and
    activated by admin are offered as delivery options.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = DeliveryZoneListSerializer

    def get_queryset(self):
        return DeliveryZone.objects.filter(status='active').order_by('area_name')


class DeliveryZoneDetailView(generics.RetrieveAPIView):
    """
    GET /api/delivery/zones/<id>/

    Get detailed information about a specific delivery zone.
    """
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = DeliveryZone.objects.filter(status='active')
    serializer_class = DeliveryZoneSerializer
    lookup_field = 'id'


class CalculateDeliveryFeeView(APIView):
    """
    POST /api/delivery/calculate/

    Calculate delivery fee based on area. Pickup orders always
    return a fee of 0 with no zone lookup.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CalculateDeliveryFeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        result = DeliveryService.calculate_delivery_fee(
            area_name=data['area_name'],
            is_pickup=data.get('is_pickup', False)
        )

        response_serializer = DeliveryFeeResponseSerializer(result)
        return Response(response_serializer.data)


class AvailableDeliveryDatesView(APIView):
    """
    POST /api/delivery/available-dates/

    Get available delivery dates and time slots.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AvailableDatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        zone_id = data.get('zone_id')
        days_ahead = data.get('days_ahead', 14)

        zone = None
        if zone_id:
            zone = get_object_or_404(DeliveryZone, id=zone_id, status='active')

        available_dates = DeliveryService.get_available_dates(zone, days_ahead)

        response_data = AvailableDateSerializer(available_dates, many=True).data
        return Response(response_data)


# ============================================================================
# ADMIN/STAFF VIEWS
# ============================================================================

class AdminDeliveryZoneListView(generics.ListCreateAPIView):
    """
    GET/POST /api/delivery/admin/zones/

    List all delivery zones or create a new one (admin only).
    Admin can freely add any area name — no predefined list.
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliveryZone.objects.all().order_by('area_name')
    serializer_class = DeliveryZoneSerializer


class AdminDeliveryZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/delivery/admin/zones/<id>/

    Retrieve, update or delete a delivery zone (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliveryZone.objects.all()
    serializer_class = DeliveryZoneSerializer
    lookup_field = 'id'


class AdminScheduleListView(generics.ListCreateAPIView):
    """
    GET/POST /api/delivery/admin/schedules/

    List all delivery schedules or create a new one (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliverySchedule.objects.all().order_by('zone', 'day_of_week', 'start_time')
    serializer_class = DeliveryScheduleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        zone_id = self.request.query_params.get('zone')
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)

        day = self.request.query_params.get('day')
        if day is not None:
            queryset = queryset.filter(day_of_week=day)

        return queryset


class AdminScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/delivery/admin/schedules/<id>/

    Retrieve, update or delete a delivery schedule (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliverySchedule.objects.all()
    serializer_class = DeliveryScheduleSerializer
    lookup_field = 'id'


class AdminExceptionListView(generics.ListCreateAPIView):
    """
    GET/POST /api/delivery/admin/exceptions/

    List all delivery exceptions or create a new one (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliveryException.objects.all().order_by('date')
    serializer_class = DeliveryExceptionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(date__year=year)

        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(date__month=month)

        exception_type = self.request.query_params.get('type')
        if exception_type:
            queryset = queryset.filter(exception_type=exception_type)

        return queryset


class AdminExceptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/delivery/admin/exceptions/<id>/

    Retrieve, update or delete a delivery exception (admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = DeliveryException.objects.all()
    serializer_class = DeliveryExceptionSerializer
    lookup_field = 'id'


class AdminZoneStatsView(APIView):
    """
    GET /api/delivery/admin/stats/

    Get delivery statistics (admin only).
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from datetime import datetime

        total_zones = DeliveryZone.objects.count()
        active_zones = DeliveryZone.objects.filter(status='active').count()

        today = datetime.now().date()
        upcoming_exceptions = DeliveryException.objects.filter(
            date__gte=today
        ).order_by('date')[:10]

        exception_serializer = DeliveryExceptionSerializer(upcoming_exceptions, many=True)

        total_schedules = DeliverySchedule.objects.count()
        active_schedules = DeliverySchedule.objects.filter(is_active=True).count()

        return Response({
            'zones': {
                'total': total_zones,
                'active': active_zones,
                'inactive': total_zones - active_zones
            },
            'schedules': {
                'total': total_schedules,
                'active': active_schedules
            },
            'upcoming_exceptions': exception_serializer.data,
            'recent_orders_delivered': 0,
        })