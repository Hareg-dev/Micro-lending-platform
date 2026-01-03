from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'amount', 'provider', 'status', 'created_at')
    list_filter = ('status', 'provider', 'created_at')
    readonly_fields = ('id', 'raw_payload', 'created_at')
    search_fields = ('reference', 'user__email')
    
    def has_delete_permission(self, request, obj=None):
        return False  # No deletes for audit trail