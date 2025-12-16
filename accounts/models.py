from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role='BORROWER'):
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(
            email=self.normalize_email(email),
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password, role='ADMIN')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('BORROWER', 'Borrower'),
        ('INVESTOR', 'Investor'),
        ('ADMIN', 'Admin'),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')

    def __str__(self):
        return f"{self.user.email} - {self.balance} {self.currency}"


# Auto-create wallet
@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance)


class LedgerEntry(models.Model):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'
    TRANSACTION_TYPES = (
        (DEBIT, 'Debit'),
        (CREDIT, 'Credit'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=6, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.wallet.user.email} - {self.transaction_type} - {self.amount}"


def transfer_funds(from_wallet, to_wallet, amount, reference=""):
    if from_wallet.balance < amount:
        raise ValueError("Insufficient balance")
    with transaction.atomic():
        # Debit sender
        from_wallet.balance -= amount
        from_wallet.save()
        LedgerEntry.objects.create(
            wallet=from_wallet,
            transaction_type=LedgerEntry.DEBIT,
            amount=amount,
            reference=reference,
            description=f"Transfer to {to_wallet.user.email}"
        )

        # Credit receiver
        to_wallet.balance += amount
        to_wallet.save()
        LedgerEntry.objects.create(
            wallet=to_wallet,
            transaction_type=LedgerEntry.CREDIT,
            amount=amount,
            reference=reference,
            description=f"Transfer from {from_wallet.user.email}"
        )


class BorrowerProfile(models.Model):
    KYC_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'BORROWER'})
    business_name = models.CharField(max_length=255, blank=True, default='')
    business_type = models.CharField(max_length=100, blank=True, null=True)
    business_age = models.PositiveIntegerField(blank=True, null=True)
    kyc_status = models.CharField(max_length=10, choices=KYC_STATUS_CHOICES, default='PENDING')
    credit_score = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.email} - {self.business_name or 'No Business Name'}"


@receiver(post_save, sender=User)
def create_borrower_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'BORROWER':
        BorrowerProfile.objects.get_or_create(user=instance)

class InvestorProfile(models.Model):
    RISK_LEVEL_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'INVESTOR'})
    risk_appetite = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='MEDIUM')
    total_invested = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email} - {self.risk_appetite}"

@receiver(post_save, sender=User)
def create_investor_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'INVESTOR':
        InvestorProfile.objects.get_or_create(user=instance)
