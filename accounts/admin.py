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


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

from .models import Wallet, LedgerEntry

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency')

@admin.register(LedgerEntry)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'timestamp', 'reference')


