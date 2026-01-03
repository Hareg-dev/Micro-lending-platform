from celery import shared_task
from django.utils import timezone
from .models import LoanListing, InvestmentBid
from loans.models import Loan
from accounts.models import Wallet


@shared_task
def create_loan_from_listing(listing_id):
    """Create loan after full funding (async)"""
    try:
        listing = LoanListing.objects.get(id=listing_id)
        
        # Prevent duplicate loan creation
        if Loan.objects.filter(application__id=listing.loan_request.id).exists():
            return "Loan already exists"
        
        # Select primary investor (largest bid)
        primary_bid = listing.investmentbid_set.filter(is_active=True).order_by('-amount').first()
        
        if not primary_bid:
            return "No active bids found"
        
        # Create loan
        loan = Loan.objects.create(
            borrower=listing.loan_request.borrower,
            investor=primary_bid.investor,
            principal=listing.loan_request.requested_amount,
            interest_rate=listing.interest_rate,
            duration_months=listing.loan_request.duration_months,
            status="ACTIVE",
            start_date=timezone.now().date()
        )
        
        # Release escrow funds
        release_escrow_funds(listing)
        
        # Generate repayment schedule
        from loans.repayment_engine import generate_repayment_schedule
        generate_repayment_schedule(loan)
        
        return f"Loan {loan.id} created successfully"
        
    except Exception as e:
        return f"Error creating loan: {str(e)}"


@shared_task
def run_credit_scoring(borrower_id):
    """Run credit scoring for borrower (async)"""
    from accounts.models import User
    from .services import calculate_hybrid_credit_score, assign_risk_grade
    
    try:
        borrower = User.objects.get(id=borrower_id)
        
        score = calculate_hybrid_credit_score(borrower)
        grade = assign_risk_grade(score)
        
        # Update borrower profile
        profile = borrower.borrowerprofile
        profile.credit_score = score
        profile.save()
        
        return f"Credit score updated: {score} (Grade: {grade})"
        
    except Exception as e:
        return f"Error in credit scoring: {str(e)}"


def release_escrow_funds(listing):
    """Release locked funds from escrow"""
    bids = listing.investmentbid_set.filter(is_active=True)
    
    for bid in bids:
        wallet = bid.investor.wallet
        wallet.locked_balance -= bid.amount
        wallet.save()
        
        # Funds already moved to borrower during disbursement
        # This just unlocks the escrow