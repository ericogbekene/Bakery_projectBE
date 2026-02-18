from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DeliveryZone, DeliveryPricingRule, 
    DeliverySchedule, DeliveryException, DeliveryService
)


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'display_order', 'code', 'name', 'base_fee', 
        'free_delivery_threshold', 'estimated_delivery_days', 
        'status', 'status_colored', 'area_count'  # Added 'status' field
    ]
    list_display_links = ['id', 'name']
    list_editable = ['display_order', 'base_fee', 'free_delivery_threshold', 'status']
    list_filter = ['status', 'estimated_delivery_days', 'rush_delivery_available']
    search_fields = ['name', 'code', 'areas']
    ordering = ['display_order', 'name']
    
    fieldsets = [
        ('Zone Identification', {
            'fields': ['name', 'code', 'description']
        }),
        ('Coverage Area', {
            'fields': ['areas'],
            'description': 'Enter areas separated by commas (e.g., "Jahi, Kado, Life Camp")'
        }),
        ('Pricing', {
            'fields': [
                'base_fee', 
                'free_delivery_threshold',
                'estimated_delivery_days'
            ]
        }),
        ('Rush Delivery', {
            'fields': ['rush_delivery_available', 'rush_delivery_premium'],
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ['status', 'display_order']
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
    
    def area_count(self, obj):
        return len(obj.area_list)
    area_count.short_description = 'Areas'
    
    # Add actions for bulk status updates
    actions = ['activate_zones', 'deactivate_zones']
    
    def activate_zones(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} zone(s) activated.')
    activate_zones.short_description = "Activate selected zones"
    
    def deactivate_zones(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} zone(s) deactivated.')
    deactivate_zones.short_description = "Deactivate selected zones"


@admin.register(DeliveryPricingRule)
class DeliveryPricingRuleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'rule_type', 'zone', 'fee_type', 'fee_value',
        'is_active', 'valid_date_range'
    ]
    list_display_links = ['id', 'name']
    list_editable = ['fee_value', 'is_active']
    list_filter = ['rule_type', 'fee_type', 'is_active', 'zone']
    search_fields = ['name', 'description']
    
    fieldsets = [
        ('Rule Information', {
            'fields': ['name', 'rule_type', 'zone', 'is_active']
        }),
        ('Conditions', {
            'fields': ['min_value', 'max_value']
        }),
        ('Fee Calculation', {
            'fields': ['fee_type', 'fee_value']
        }),
        ('Applicability', {
            'fields': ['applies_to_rush', 'applies_to_regular']
        }),
        ('Validity Period', {
            'fields': ['valid_from', 'valid_until'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def valid_date_range(self, obj):
        if obj.valid_from and obj.valid_until:
            return f"{obj.valid_from.strftime('%Y-%m-%d')} to {obj.valid_until.strftime('%Y-%m-%d')}"
        elif obj.valid_from:
            return f"From {obj.valid_from.strftime('%Y-%m-%d')}"
        elif obj.valid_until:
            return f"Until {obj.valid_until.strftime('%Y-%m-%d')}"
        return "Always"
    valid_date_range.short_description = 'Validity'


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
    search_fields = ['zone__name', 'time_slot_name']
    
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
    
    # Add action to reset daily counters
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
        return ", ".join([z.code for z in zones])
    affected_zones.short_description = 'Affected Zones'