from accounts.models import BorrowerProfile


def calculate_risk_score(borrower_profile):
    """Simple rule-based risk scoring"""
    score = 500  # Base score
    
    # Business age factor
    if borrower_profile.business_age:
        if borrower_profile.business_age >= 5:
            score += 100
        elif borrower_profile.business_age >= 2:
            score += 50
    
    # KYC status
    if borrower_profile.kyc_status == 'VERIFIED':
        score += 150
    elif borrower_profile.kyc_status == 'PENDING':
        score += 0
    else:  # REJECTED
        score -= 200
    
    # Wallet balance (basic liquidity check)
    wallet_balance = borrower_profile.user.wallet.balance
    if wallet_balance > 1000:
        score += 100
    elif wallet_balance > 500:
        score += 50
    
    return max(300, min(850, score))  # Cap between 300-850


def update_borrower_risk_score(borrower_profile):
    """Update and save risk score"""
    borrower_profile.credit_score = calculate_risk_score(borrower_profile)
    borrower_profile.save(update_fields=['credit_score'])
    return borrower_profile.credit_score