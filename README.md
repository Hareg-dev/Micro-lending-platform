# Micro-Lending Platform

A Django-based FinTech platform for peer-to-peer lending with enterprise-grade security and compliance.

## Architecture

### Core Apps
- **accounts**: User management, wallets, profiles
- **loans**: Loan applications, approvals, repayments
- **risk**: Credit scoring and risk assessment
- **compliance**: Audit logging and regulatory compliance

### Key Features
- ✅ Role-based access (Borrower/Investor/Admin)
- ✅ Atomic money transfers with ledger trails
- ✅ Automated loan approval workflow
- ✅ Risk scoring engine
- ✅ Comprehensive audit logging
- ✅ Django Admin for oversight

## Quick Start

1. **Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

2. **Test System**
   ```bash
   python test_system.py
   ```

3. **Access Admin**
   - URL: http://localhost:8000/admin/
   - Login: admin@test.com / admin123

## API Endpoints

- `/loans/apply/` - Loan application form
- `/loans/dashboard/` - User dashboard
- `/loans/approve/<id>/` - Approve loan (investors)
- `/admin/` - Full system administration

## Security Features

- Atomic database transactions
- Immutable ledger entries
- Audit trail for all operations
- Role-based permissions
- IP tracking for sensitive actions

## System Flow

1. User registers → Wallet auto-created
2. Borrower applies for loan
3. Risk engine calculates score
4. Investor approves loan
5. Funds transferred atomically
6. Repayment schedule generated
7. All actions logged for compliance

## Database Models

### User & Profiles
- Custom User with roles
- BorrowerProfile (KYC, credit score)
- InvestorProfile (risk appetite)

### Financial
- Wallet (balance, currency)
- LedgerEntry (immutable transaction log)
- LoanApplication → Loan → Repayment

### Compliance
- AuditLog (all system actions)
- ComplianceAlert (risk monitoring)

## Production Considerations

- Use PostgreSQL for production
- Enable SSL/TLS
- Configure proper logging
- Set up monitoring alerts
- Implement rate limiting
- Add payment gateway integration