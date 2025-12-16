import requests
from django.conf import settings
from django.db import transaction
from .models import TelebirrTransaction
from accounts.models import transfer_funds, LedgerEntry


class TelebirrAPI:
    def __init__(self):
        self.base_url = getattr(settings, 'TELEBIRR_BASE_URL', 'https://api.telebirr.com')
        self.app_id = getattr(settings, 'TELEBIRR_APP_ID', 'your_app_id')
        self.app_key = getattr(settings, 'TELEBIRR_APP_KEY', 'your_app_key')
    
    def initiate_payment(self, phone, amount, reference):
        """Initiate Telebirr payment"""
        payload = {
            'appId': self.app_id,
            'phoneNumber': phone,
            'amount': str(amount),
            'reference': reference,
        }
        
        # Mock response for development
        return {
            'status': 'SUCCESS',
            'transactionId': f'TB_{reference}',
            'message': 'Payment initiated'
        }
    
    def verify_payment(self, transaction_id):
        """Verify payment status"""
        # Mock verification for development
        return {
            'status': 'SUCCESS',
            'transactionId': transaction_id,
            'amount': '1000.00'
        }


def process_deposit(user, amount, phone_number):
    """Process wallet deposit via Telebirr"""
    telebirr = TelebirrAPI()
    
    # Create transaction record
    tx = TelebirrTransaction.objects.create(
        user=user,
        wallet=user.wallet,
        amount=amount,
        telebirr_ref=f'DEP_{user.id}_{TelebirrTransaction.objects.count()}',
        phone_number=phone_number
    )
    
    # Initiate payment
    response = telebirr.initiate_payment(phone_number, amount, tx.telebirr_ref)
    
    if response['status'] == 'SUCCESS':
        tx.status = 'SUCCESS'
        tx.save()
        
        # Credit wallet
        with transaction.atomic():
            user.wallet.balance += amount
            user.wallet.save()
            LedgerEntry.objects.create(
                wallet=user.wallet,
                transaction_type=LedgerEntry.CREDIT,
                amount=amount,
                reference=tx.telebirr_ref,
                description=f"Telebirr deposit from {phone_number}"
            )
    
    return tx