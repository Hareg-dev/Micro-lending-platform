from django.contrib import admin
from .models import LoanApplication, Loan, Repayment


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'amount', 'duration_months', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'borrower', 'investor', 'principal', 'status', 'start_date')
    list_filter = ('status', 'start_date')
    readonly_fields = ('start_date',)


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'due_date', 'status', 'paid_date')
    list_filter = ('status', 'due_date')