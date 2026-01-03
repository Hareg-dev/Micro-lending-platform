import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import PaymentTransaction
from loans.models import Loan
from loans.repayment_engine import process_repayment


@csrf_exempt
def telebirr_repayment_webhook(request):
    """Handle Telebirr repayment webhooks"""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    reference = payload.get("outTradeNo")
    status = payload.get("tradeStatus")
    amount = payload.get("totalAmount")

    if not reference or not reference.startswith("REPAY_"):
        return HttpResponseBadRequest("Invalid repayment reference")

    # Extract loan ID from reference (format: REPAY_LOAN_123)
    try:
        loan_id = reference.split("_")[-1]
        loan = Loan.objects.get(id=loan_id, status="ACTIVE")
    except (Loan.DoesNotExist, IndexError):
        return HttpResponseBadRequest("Invalid loan")

    # Check if already processed (idempotent)
    if loan.repayment_transactions.filter(telebirr_ref=reference).exists():
        return JsonResponse({"status": "OK"})

    if status != "SUCCESS":
        return JsonResponse({"status": "FAILED"})

    try:
        with transaction.atomic():
            # Process the repayment
            repayment_tx = process_repayment(
                loan=loan,
                amount=Decimal(amount),
                reference=reference
            )
            
            # Link to Telebirr reference
            repayment_tx.telebirr_ref = reference
            repayment_tx.save()

        return JsonResponse({"status": "SUCCESS"})
    
    except Exception as e:
        return JsonResponse({"status": "ERROR", "message": str(e)}, status=400)