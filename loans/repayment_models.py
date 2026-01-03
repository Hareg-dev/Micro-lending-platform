from django.db import models
from decimal import Decimal
from datetime import timedelta
from .models import Loan
from accounts.models import User


class RepaymentSchedule(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="schedule")
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    
    principal_due = models.DecimalField(max_digits=12, decimal_places=2)
    interest_due = models.DecimalField(max_digits=12, decimal_places=2)
    
    paid_principal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_fully_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ("loan", "installment_number")
    
    @property
    def total_due(self):
        return self.principal_due + self.interest_due
    
    @property
    def total_paid(self):
        return self.paid_principal + self.paid_interest
    
    @property
    def remaining_amount(self):
        return self.total_due - self.total_paid


class RepaymentTransaction(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayment_transactions")
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    telebirr_ref = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Repayment {self.reference} - {self.amount} ETB"


class LateFee(models.Model):
    schedule = models.OneToOneField(RepaymentSchedule, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Late fee {self.amount} ETB for installment {self.schedule.installment_number}"