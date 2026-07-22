from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DeliveryZone, DeliverySchedule, DeliveryException, DeliveryService
)


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    """
    Admin can freely add, rename, or remove delivery areas here —
    there's no predefined list of neighborhoods. Only zones with
    status='active' show up on the frontend dropdown.
    """
    list_display = [
        'id', 'area_name', 'fee', 'status', 'status_colored', 'updated_at'
    ]
    list_display_links = ['id', 'area_name']
    list_editable = ['fee', 'status']
    list_filter = ['status']
    search_fields = ['area_name']
    ordering = ['area_name']

    fieldsets = [
        ('Zone', {
            'fields': ['area_name', 'fee', 'status']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at']

    def status_colored(self, obj):
        colors = {
            'active': 'green',
            'inactive': 'red',
            'temporary': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Status'

    actions = ['activate_zones', 'deactivate_zones']

    def activate_zones(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} zone(s) activated.')
    activate_zones.short_description = "Activate selected zones"

    def deactivate_zones(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} zone(s) deactivated.')
    deactivate_zones.short_description = "Deactivate selected zones"


@admin.register(DeliverySchedule)
class DeliveryScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'zone', 'get_day_of_week_display', 'time_slot_name',
        'start_time', 'end_time', 'max_orders_per_slot', 'current_orders',
        'capacity_status', 'is_active'
    ]
    list_display_links = ['id', 'zone']
    list_editable = ['max_orders_per_slot', 'current_orders', 'is_active']
    list_filter = ['zone', 'day_of_week', 'is_active']
    search_fields = ['zone__area_name', 'time_slot_name']

    fieldsets = [
        ('Zone & Day', {
            'fields': ['zone', 'day_of_week']
        }),
        ('Time Slot', {
            'fields': ['time_slot_name', 'start_time', 'end_time']
        }),
        ('Capacity', {
            'fields': ['max_orders_per_slot', 'current_orders']
        }),
        ('Status', {
            'fields': ['is_active']
        }),
    ]

    def capacity_status(self, obj):
        remaining = obj.slots_remaining
        total = obj.max_orders_per_slot

        if remaining == 0:
            color = 'red'
            status = 'Full'
        elif remaining <= total * 0.2:
            color = 'orange'
            status = f'Almost Full ({remaining} left)'
        else:
            color = 'green'
            status = f'Available ({remaining} slots)'

        return format_html(
            '<span style="color: {};">{}</span>',
            color, status
        )
    capacity_status.short_description = 'Capacity'

    actions = ['reset_daily_counters']

    def reset_daily_counters(self, request, queryset):
        updated = queryset.update(current_orders=0)
        self.message_user(request, f'{updated} schedule(s) counters reset.')
    reset_daily_counters.short_description = "Reset daily order counters"


@admin.register(DeliveryException)
class DeliveryExceptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'title', 'exception_type', 'delivery_available', 'affected_zones']
    list_display_links = ['id', 'title']
    list_editable = ['delivery_available']
    list_filter = ['exception_type', 'delivery_available', 'date']
    search_fields = ['title', 'description']
    date_hierarchy = 'date'

    fieldsets = [
        ('Exception Details', {
            'fields': ['date', 'exception_type', 'title', 'description']
        }),
        ('Affected Zones', {
            'fields': ['zones'],
            'description': 'Leave empty to apply to all zones'
        }),
        ('Delivery Modifications', {
            'fields': ['delivery_available', 'modified_fee', 'modified_schedule']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at']

    def affected_zones(self, obj):
        zones = obj.zones.all()
        if not zones:
            return "All Zones"
        return ", ".join([z.area_name for z in zones])
    affected_zones.short_description = 'Affected Zones'