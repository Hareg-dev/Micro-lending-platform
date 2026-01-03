from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .repayment_models import RepaymentSchedule, RepaymentTransaction, LateFee
from accounts.models import Wallet, LedgerEntry


def generate_repayment_schedule(loan):
    """Generate EMI repayment schedule for loan"""
    monthly_rate = (loan.interest_rate / Decimal("100")) / 12
    n = loan.duration_months
    P = loan.principal

    # EMI calculation
    emi = (P * monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
    
    remaining = P
    schedules = []

    for i in range(1, n + 1):
        interest = remaining * monthly_rate
        principal = emi - interest
        remaining -= principal

        schedules.append(
            RepaymentSchedule(
                loan=loan,
                installment_number=i,
                due_date=loan.start_date + timedelta(days=30 * i),
                principal_due=principal,
                interest_due=interest,
            )
        )

    RepaymentSchedule.objects.bulk_create(schedules)


@transaction.atomic
def process_repayment(loan, amount, reference):
    """Process repayment with proper allocation"""
    # Create repayment transaction
    repayment_tx = RepaymentTransaction.objects.create(
        loan=loan,
        borrower=loan.borrower,
        amount=amount,
        reference=reference
    )
    
    # Get unpaid schedules in order
    schedules = loan.schedule.filter(is_fully_paid=False).order_by("installment_number")
    
    remaining = amount
    
    for schedule in schedules:
        if remaining <= 0:
            break
        
        # Apply to interest first
        interest_due = schedule.interest_due - schedule.paid_interest
        interest_payment = min(remaining, interest_due)
        schedule.paid_interest += interest_payment
        remaining -= interest_payment
        
        # Then apply to principal
        principal_due = schedule.principal_due - schedule.paid_principal
        principal_payment = min(remaining, principal_due)
        schedule.paid_principal += principal_payment
        remaining -= principal_payment
        
        # Check if fully paid
        if (schedule.paid_interest == schedule.interest_due and 
            schedule.paid_principal == schedule.principal_due):
            schedule.is_fully_paid = True
        
        schedule.save()
    
    # Update wallet balances
    apply_repayment_funds(loan, amount, reference)
    
    # Check if loan is completed
    if not loan.schedule.filter(is_fully_paid=False).exists():
        loan.status = "COMPLETED"
        loan.save(update_fields=["status"])
    
    return repayment_tx


@transaction.atomic
def apply_repayment_funds(loan, amount, reference):
    """Move funds from borrower to investor"""
    borrower_wallet = Wallet.objects.select_for_update().get(user=loan.borrower)
    investor_wallet = Wallet.objects.select_for_update().get(user=loan.investor)
    
    if borrower_wallet.balance < amount:
        raise ValueError("Insufficient balance for repayment")
    
    borrower_wallet.balance -= amount
    investor_wallet.balance += amount
    
    borrower_wallet.save(update_fields=["balance"])
    investor_wallet.save(update_fields=["balance"])
    
    # Create ledger entries
    LedgerEntry.objects.create(
        wallet=borrower_wallet,
        amount=-amount,
        entry_type=LedgerEntry.Type.LOAN_REPAYMENT,
        transaction_type='DEBIT',
        reference=reference
    )
    
    LedgerEntry.objects.create(
        wallet=investor_wallet,
        amount=amount,
        entry_type=LedgerEntry.Type.LOAN_REPAYMENT,
        transaction_type='CREDIT',
        reference=reference
    )


def apply_late_fees():
    """Apply late fees to overdue installments"""
    from django.utils import timezone
    
    overdue_schedules = RepaymentSchedule.objects.filter(
        due_date__lt=timezone.now().date(),
        is_fully_paid=False
    )
    
    for schedule in overdue_schedules:
        LateFee.objects.get_or_create(
            schedule=schedule,
            defaults={"amount": schedule.principal_due * Decimal("0.01")}  # 1% late fee
        )


def calculate_investor_roi(investor):
    """Calculate investor ROI from repayments"""
    from django.db.models import Sum
    
    # Total interest earned
    interest_earned = LedgerEntry.objects.filter(
        wallet__user=investor,
        entry_type=LedgerEntry.Type.LOAN_REPAYMENT,
        transaction_type='CREDIT'
    ).aggregate(Sum("amount"))["amount__sum"] or 0
    
    # Total principal invested
    from .models import Loan
    principal_invested = Loan.objects.filter(
        investor=investor
    ).aggregate(Sum("principal"))["principal__sum"] or 1
    
    return (interest_earned / principal_invested) * 100