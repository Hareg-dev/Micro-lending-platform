from django.contrib import admin
from .models import User
from .models import Wallet
from django.db.models.signals import post_save
from django.dispatch import receiver


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active')
    search_fields = ('email',)


# Wallet creation moved to models.py to avoid duplication

from .models import Wallet, LedgerEntry

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency')

@admin.register(LedgerEntry)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'timestamp', 'reference')


from .models import BorrowerProfile, InvestorProfile

@admin.register(BorrowerProfile)
class BorrowerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'kyc_status', 'credit_score')
    list_filter = ('kyc_status',)
    search_fields = ('user__email', 'business_name')


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_appetite', 'total_invested')
    list_filter = ('risk_appetite',)
    search_fields = ('user__email',)
