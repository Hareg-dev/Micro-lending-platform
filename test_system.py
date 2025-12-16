#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, Wallet
from loans.models import LoanApplication
from loans.services import approve_loan
from risk.scoring import update_borrower_risk_score

# Create test users
borrower, _ = User.objects.get_or_create(
    email='borrower@test.com',
    defaults={'role': 'BORROWER'}
)
investor, _ = User.objects.get_or_create(
    email='investor@test.com', 
    defaults={'role': 'INVESTOR'}
)
if not borrower.check_password('pass123'):
    borrower.set_password('pass123')
    borrower.save()
if not investor.check_password('pass123'):
    investor.set_password('pass123')
    investor.save()

# Add funds to investor
investor.wallet.balance = 10000
investor.wallet.save()

# Update borrower risk score
if hasattr(borrower, 'borrowerprofile'):
    update_borrower_risk_score(borrower.borrowerprofile)
else:
    print("No borrower profile found - signals may not have fired")

# Create loan application
app = LoanApplication.objects.create(
    borrower=borrower,
    amount=5000,
    duration_months=12,
    purpose="Business expansion"
)

# Approve loan
loan = approve_loan(app, investor)

print("System test complete!")
print(f"Loan #{loan.id} approved: ${loan.principal}")
print(f"Borrower balance: ${borrower.wallet.balance}")
print(f"Investor balance: ${investor.wallet.balance}")
if hasattr(borrower, 'borrowerprofile'):
    print(f"Risk score: {borrower.borrowerprofile.credit_score}")
else:
    print("Risk score: N/A (no profile)")