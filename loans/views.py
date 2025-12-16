from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import LoanApplication, Loan
from .services import approve_loan
from accounts.models import User


@login_required
def apply_loan(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        duration = request.POST.get('duration_months')
        purpose = request.POST.get('purpose')
        
        LoanApplication.objects.create(
            borrower=request.user,
            amount=amount,
            duration_months=duration,
            purpose=purpose
        )
        messages.success(request, 'Loan application submitted')
        return redirect('loan_dashboard')
    
    return render(request, 'loans/apply.html')


@login_required
def loan_dashboard(request):
    if request.user.role == 'BORROWER':
        applications = LoanApplication.objects.filter(borrower=request.user)
        loans = Loan.objects.filter(borrower=request.user)
    else:
        applications = LoanApplication.objects.filter(status='PENDING')
        loans = Loan.objects.filter(investor=request.user)
    
    return render(request, 'loans/dashboard.html', {
        'applications': applications,
        'loans': loans
    })


@login_required
def approve_loan_view(request, app_id):
    if request.user.role != 'INVESTOR':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    application = get_object_or_404(LoanApplication, id=app_id, status='PENDING')
    
    try:
        loan = approve_loan(application, request.user)
        return JsonResponse({'success': True, 'loan_id': loan.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)