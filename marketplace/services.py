from django.db import transaction
from decimal import Decimal
from .models import LoanRequest, LoanListing, InvestmentBid
from accounts.models import Wallet
from risk.scoring import calculate_risk_score


def create_loan_listing(loan_request, interest_rate):
    """Create marketplace listing from approved loan request"""
    if loan_request.status != "APPROVED":
        raise ValueError("Loan request must be approved first")
    
    listing = LoanListing.objects.create(
        loan_request=loan_request,
        interest_rate=interest_rate,
        min_bid=Decimal("1000")
    )
    return listing


@transaction.atomic
def place_investment_bid(investor, listing, amount):
    """Place investment bid with escrow locking"""
    if not listing.is_open:
        raise ValueError("Listing is closed")
    
    if amount < listing.min_bid:
        raise ValueError(f"Minimum bid is {listing.min_bid} ETB")
    
    wallet = Wallet.objects.select_for_update().get(user=investor)
    
    if wallet.available_balance < amount:
        raise ValueError("Insufficient available balance")
    
    # Lock funds in escrow
    wallet.balance -= amount
    wallet.locked_balance += amount
    wallet.save()
    
    # Create or update bid
    bid, created = InvestmentBid.objects.get_or_create(
        investor=investor,
        listing=listing,
        defaults={'amount': amount}
    )
    
    if not created:
        # Update existing bid
        old_amount = bid.amount
        bid.amount = amount
        bid.save()
        
        # Adjust locked balance
        difference = amount - old_amount
        wallet.balance -= difference
        wallet.locked_balance += difference
        wallet.save()
    
    # Update listing funded amount
    from django.db.models import Sum
    listing.funded_amount = listing.investmentbid_set.filter(is_active=True).aggregate(
        total=Sum('amount')
    )['total'] or 0
    listing.save()
    
    # Check if fully funded
    check_listing_funded(listing)
    
    return bid


def check_listing_funded(listing):
    """Check if listing is fully funded and activate loan"""
    if listing.funded_amount >= listing.loan_request.requested_amount:
        listing.is_open = False
        listing.loan_request.status = "FUNDED"
        listing.save()
        listing.loan_request.save()
        
        # Trigger loan creation (sync for testing)
        from .tasks import create_loan_from_listing
        try:
            create_loan_from_listing.delay(listing.id)
        except:
            # Fallback to sync execution for testing
            create_loan_from_listing(listing.id)


def calculate_hybrid_credit_score(borrower):
    """Hybrid rule-based + ML credit scoring"""
    # Rule-based component
    rule_score = 500
    profile = borrower.borrowerprofile
    
    if profile.business_age and profile.business_age > 3:
        rule_score += 100
    
    if profile.kyc_status == 'VERIFIED':
        rule_score += 150
    
    wallet_balance = borrower.wallet.balance
    if wallet_balance > 10000:
        rule_score += 100
    elif wallet_balance > 5000:
        rule_score += 50
    
    # ML component (simplified)
    ml_score = calculate_risk_score(profile)
    
    # Combine scores
    final_score = int((rule_score + ml_score) / 2)
    return min(final_score, 900)


def assign_risk_grade(score):
    """Convert credit score to risk grade"""
    if score >= 800:
        return "A"
    elif score >= 700:
        return "B"
    elif score >= 600:
        return "C"
    else:
        return "D"