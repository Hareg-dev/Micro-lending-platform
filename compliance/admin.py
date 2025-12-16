from django.contrib import admin
from .models import AuditLog, ComplianceAlert


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    readonly_fields = ('user', 'action', 'content_type', 'object_id', 'details', 'ip_address', 'timestamp')
    search_fields = ('user__email',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComplianceAlert)
class ComplianceAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'user', 'resolved', 'created_at')
    list_filter = ('severity', 'resolved', 'created_at')
    search_fields = ('title', 'user__email')