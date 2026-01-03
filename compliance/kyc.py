from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from accounts.models import LedgerEntry

User = get_user_model()

MAX_DAILY_DEPOSIT = 50000  # ETB


class KYCProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    national_id = models.CharField(max_length=50)
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {'Verified' if self.verified else 'Pending'}"


def check_limits(user, amount):
    """Check daily deposit limits for NBE compliance"""
    today_total = LedgerEntry.objects.filter(
        wallet__user=user,
        entry_type=LedgerEntry.Type.DEPOSIT,
        created_at__date=timezone.now().date()
    ).aggregate(Sum("amount"))["amount__sum"] or 0

    if today_total + amount > MAX_DAILY_DEPOSIT:
        raise ValueError("Daily limit exceeded")


def freeze_wallet(user, reason="Compliance review"):
    """Freeze user wallet for compliance"""
    from accounts.models import Wallet
    wallet = Wallet.objects.get(user=user)
    wallet.status = Wallet.Status.FROZEN
    wallet.save()
    
    from .models import ComplianceAlert
    ComplianceAlert.objects.create(
        title="Wallet Frozen",
        description=f"Wallet frozen for user {user.email}. Reason: {reason}",
        severity="HIGH",
        user=user
    )