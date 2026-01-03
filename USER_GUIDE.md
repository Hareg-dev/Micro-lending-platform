# Micro-Lending Platform - User Guide

## Quick Start

### 1. System Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### 2. Access Points
- **Admin Panel**: http://localhost:8000/admin/
- **Marketplace**: http://localhost:8000/marketplace/
- **Loan Dashboard**: http://localhost:8000/loans/dashboard/

## User Roles

### Borrower Workflow
1. **Register Account** → Auto-creates wallet & profile
2. **Submit Loan Request** → `/marketplace/request/`
3. **Wait for Approval** → Admin reviews credit score
4. **Loan Listed** → Appears in marketplace
5. **Get Funded** → Investors bid until fully funded
6. **Receive Funds** → Automatic disbursement to wallet
7. **Make Repayments** → Via Telebirr or wallet balance

### Investor Workflow
1. **Register Account** → Auto-creates wallet
2. **Fund Wallet** → Via Telebirr deposits
3. **Browse Marketplace** → View loan listings with risk grades
4. **Place Bids** → Funds locked in escrow
5. **Earn Returns** → Receive repayments with interest

### Admin Operations
1. **Review Loan Requests** → Approve/reject based on credit scores
2. **Monitor Marketplace** → Track funding progress
3. **Manage Compliance** → View audit logs, freeze wallets
4. **Handle Disputes** → Manual overrides and adjustments

## Key Features

### Telebirr Integration
- **Deposits**: `/payments/webhook/telebirr/`
- **Repayments**: `/payments/webhook/repayment/`
- **Reference Format**: `REPAY_LOAN_{id}` for repayments

### Credit Scoring
- **Hybrid System**: Rule-based + ML scoring
- **Risk Grades**: A (800+), B (700+), C (600+), D (<600)
- **Auto-calculated** on loan request submission

### Escrow System
- **Bid Placement**: Funds locked until loan activation
- **Partial Funding**: Multiple investors per loan
- **Auto-activation**: When 100% funded

### Repayment Engine
- **EMI Calculation**: Industry-standard formula
- **Payment Allocation**: Interest first, then principal
- **Late Fees**: 1% daily penalty (run `python manage.py apply_late_fees`)

## API Endpoints

### Core Operations
```
POST /loans/apply/              # Submit loan application
GET  /loans/dashboard/          # User dashboard
POST /loans/approve/<id>/       # Approve loan (investors)
POST /marketplace/bid/<id>/     # Place investment bid
```

### Webhooks
```
POST /payments/webhook/telebirr/    # Telebirr deposits
POST /payments/webhook/repayment/   # Telebirr repayments
```

## Testing

### System Tests
```bash
# Test complete loan flow
python test_system.py

# Test repayment engine
python test_repayment_engine.py

# Test marketplace bidding
python test_marketplace.py

# Test Telebirr webhooks
python test_telebirr.py
```

### Sample Data
```bash
# Create test users and transactions
python manage.py shell -c "
from accounts.models import User
borrower = User.objects.create_user('test@example.com', 'pass', 'BORROWER')
investor = User.objects.create_user('investor@example.com', 'pass', 'INVESTOR')
"
```

## Maintenance

### Daily Operations
```bash
# Apply late fees (run daily)
python manage.py apply_late_fees

# Check system health
python manage.py shell -c "
from accounts.models import Wallet, LedgerEntry
print(f'Total wallets: {Wallet.objects.count()}')
print(f'Total transactions: {LedgerEntry.objects.count()}')
"
```

### Monitoring
- **Audit Logs**: Admin → Compliance → Audit Log
- **Payment Transactions**: Admin → Payments → Payment Transaction
- **Loan Status**: Admin → Loans → Loan
- **Marketplace Activity**: Admin → Marketplace → Investment Bid

## Troubleshooting

### Common Issues
1. **Migration Errors**: Run `python manage.py migrate --fake-initial`
2. **Celery Tasks Failing**: Ensure Redis is running or tasks run synchronously
3. **Telebirr Webhooks**: Check reference format and payload structure
4. **Balance Mismatches**: Verify ledger entries match wallet balances

### Debug Commands
```bash
# Check wallet consistency
python manage.py shell -c "
from accounts.models import Wallet, LedgerEntry
for wallet in Wallet.objects.all():
    ledger_sum = sum(entry.amount for entry in wallet.ledgerentry_set.all())
    if wallet.balance != ledger_sum:
        print(f'Mismatch: {wallet.user.email}')
"

# View recent transactions
python manage.py shell -c "
from accounts.models import LedgerEntry
for entry in LedgerEntry.objects.order_by('-created_at')[:10]:
    print(f'{entry.wallet.user.email}: {entry.amount} ETB - {entry.entry_type}')
"
```

## Security Notes

- All financial operations are atomic
- Ledger entries are immutable (no deletes)
- Rate limiting active on sensitive endpoints
- IP tracking for compliance
- Wallet freeze capability for risk management
- Daily transaction limits enforced