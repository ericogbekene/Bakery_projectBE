from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("email", "amount", "reference", "status", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("email", "reference")
    actions = ["mark_as_refunded"]

    @admin.action(description="Mark selected transactions as refunded")
    def mark_as_refunded(self, request, queryset):
        queryset.update(status="refunded")

