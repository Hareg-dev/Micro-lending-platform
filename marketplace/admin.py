from django.contrib import admin
from .models import LoanRequest, LoanListing, InvestmentBid


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'requested_amount', 'risk_grade', 'status', 'created_at')
    list_filter = ('status', 'risk_grade', 'created_at')
    readonly_fields = ('credit_score', 'created_at')
    actions = ['approve_requests']
    
    def approve_requests(self, request, queryset):
        from .services import create_loan_listing
        for loan_request in queryset.filter(status='PENDING'):
            loan_request.status = 'APPROVED'
            loan_request.save()
            create_loan_listing(loan_request, 12.0)  # Default 12% interest
        self.message_user(request, f'{queryset.count()} requests approved')
    approve_requests.short_description = "Approve selected requests"


@admin.register(LoanListing)
class LoanListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan_request', 'interest_rate', 'funded_amount', 'funding_progress', 'is_open')
    list_filter = ('is_open', 'created_at')
    readonly_fields = ('funded_amount', 'created_at')


@admin.register(InvestmentBid)
class InvestmentBidAdmin(admin.ModelAdmin):
    list_display = ('investor', 'listing', 'amount', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)