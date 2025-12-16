from django.core.mail import send_mail
from django.conf import settings
import requests
from .models import Notification


def send_email(user, title, message):
    """Send email notification"""
    try:
        send_mail(
            title,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        Notification.objects.create(
            user=user,
            type='EMAIL',
            title=title,
            message=message,
            sent=True
        )
        return True
    except Exception:
        Notification.objects.create(
            user=user,
            type='EMAIL',
            title=title,
            message=message,
            sent=False
        )
        return False


def send_sms(user, message, phone=None):
    """Send SMS notification via Ethiopian SMS gateway"""
    phone_number = phone or getattr(user, 'phone_number', None)
    if not phone_number:
        return False
    
    # Mock SMS API for Ethiopian providers
    try:
        # Replace with actual SMS gateway
        payload = {
            'to': phone_number,
            'message': message,
            'api_key': getattr(settings, 'SMS_API_KEY', 'your_key')
        }
        
        # Mock success for development
        success = True
        
        Notification.objects.create(
            user=user,
            type='SMS',
            title='SMS Notification',
            message=message,
            sent=success
        )
        return success
    except Exception:
        return False


def notify_loan_approved(loan):
    """Send loan approval notifications"""
    send_email(
        loan.borrower,
        'Loan Approved',
        f'Your loan of ${loan.principal} has been approved!'
    )
    
    send_email(
        loan.investor,
        'Investment Confirmed',
        f'You have invested ${loan.principal} in loan #{loan.id}'
    )