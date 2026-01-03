import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import PaymentTransaction
from accounts.models import Wallet, LedgerEntry


@csrf_exempt
def telebirr_webhook(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    reference = payload.get("outTradeNo")
    status = payload.get("tradeStatus")
    amount = payload.get("totalAmount")

    if not reference:
        return HttpResponseBadRequest("Missing reference")

    try:
        txn = PaymentTransaction.objects.select_for_update().get(reference=reference)
    except PaymentTransaction.DoesNotExist:
        return HttpResponseBadRequest("Unknown transaction")

    if txn.status == PaymentTransaction.Status.SUCCESS:
        return JsonResponse({"status": "OK"})  # idempotent

    if status != "SUCCESS":
        txn.status = PaymentTransaction.Status.FAILED
        txn.raw_payload = payload
        txn.save()
        return JsonResponse({"status": "FAILED"})

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(user=txn.user)

        wallet.balance += txn.amount
        wallet.save(update_fields=["balance"])

        LedgerEntry.objects.create(
            wallet=wallet,
            amount=txn.amount,
            entry_type=LedgerEntry.Type.DEPOSIT,
            reference=txn.reference
        )

        txn.status = PaymentTransaction.Status.SUCCESS
        txn.raw_payload = payload
        txn.save(update_fields=["status", "raw_payload"])

    return JsonResponse({"status": "SUCCESS"})