from django.db import transaction
from django.utils import timezone
from .models import Repayment
from accounts.models import transfer_funds


def process_repayment(repayment_id, amount=None):
    """Process loan repayment"""
    repayment = Repayment.objects.get(id=repayment_id)
    
    if repayment.status == 'PAID':
        raise ValueError("Repayment already processed")
    
    payment_amount = amount or repayment.amount
    
    with transaction.atomic():
        # Transfer funds from borrower to investor
        transfer_funds(
            repayment.loan.borrower.wallet,
            repayment.loan.investor.wallet,
            payment_amount,
            f"Repayment #{repayment.id}"
        )
        
        # Mark as paid
        repayment.status = 'PAID'
        repayment.paid_date = timezone.now()
        repayment.save()
        
        # Check if loan is fully paid
        if not repayment.loan.repayments.filter(status='PENDING').exists():
            repayment.loan.status = 'COMPLETED'
            repayment.loan.save()
    
    return repayment