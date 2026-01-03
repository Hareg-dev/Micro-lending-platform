from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class LoanRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
        ("FUNDED", "FUNDED"),
    ]
    
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_amount = models.DecimalField(max_digits=14, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    purpose = models.TextField()
    credit_score = models.PositiveIntegerField(default=0)
    risk_grade = models.CharField(max_length=5, default="D")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.borrower.email} - {self.requested_amount} ETB"


class LoanListing(models.Model):
    loan_request = models.OneToOneField(LoanRequest, on_delete=models.CASCADE)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    min_bid = models.DecimalField(max_digits=12, decimal_places=2, default=1000)
    funded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Listing {self.id} - {self.loan_request.requested_amount} ETB"

    @property
    def funding_progress(self):
        return (self.funded_amount / self.loan_request.requested_amount) * 100


class InvestmentBid(models.Model):
    investor = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(LoanListing, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('investor', 'listing')

    def __str__(self):
        return f"{self.investor.email} - {self.amount} ETB"