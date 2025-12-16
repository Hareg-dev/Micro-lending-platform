from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import LoanApplication, Loan, Repayment
from accounts.models import transfer_funds


def approve_loan(application, investor, interest_rate=Decimal('12.00')):
    """Approve loan application and disburse funds"""
    if application.status != 'PENDING':
        raise ValueError("Application already processed")
    
    with transaction.atomic():
        # Calculate monthly payment
        monthly_rate = interest_rate / 100 / 12
        num_payments = application.duration_months
        monthly_payment = (application.amount * monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        # Create loan
        loan = Loan.objects.create(
            application=application,
            borrower=application.borrower,
            investor=investor,
            principal=application.amount,
            interest_rate=interest_rate,
            duration_months=application.duration_months,
            monthly_payment=monthly_payment,
            end_date=timezone.now() + timedelta(days=30 * application.duration_months)
        )
        
        # Transfer funds
        transfer_funds(
            investor.wallet,
            application.borrower.wallet,
            application.amount,
            f"Loan disbursement #{loan.id}"
        )
        
        # Update application
        application.status = 'APPROVED'
        application.reviewed_at = timezone.now()
        application.save()
        
        # Create repayment schedule
        create_repayment_schedule(loan)
        
        # Send notifications
        from notifications.services import notify_loan_approved
        notify_loan_approved(loan)
        
        return loan


def create_repayment_schedule(loan):
    """Create monthly repayment schedule"""
    for month in range(1, loan.duration_months + 1):
        due_date = loan.start_date.date() + timedelta(days=30 * month)
        Repayment.objects.create(
            loan=loan,
            amount=loan.monthly_payment,
            due_date=due_date
        )