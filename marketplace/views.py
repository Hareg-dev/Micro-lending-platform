from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .models import LoanListing, LoanRequest
from .services import place_investment_bid, create_loan_listing, calculate_hybrid_credit_score, assign_risk_grade


def marketplace_view(request):
    """Display open loan listings"""
    listings = LoanListing.objects.filter(is_open=True).select_related('loan_request__borrower')
    return render(request, 'marketplace/listings.html', {'listings': listings})


@login_required
def place_bid_view(request, listing_id):
    """Place investment bid"""
    if request.method == 'POST':
        listing = get_object_or_404(LoanListing, id=listing_id, is_open=True)
        amount = request.POST.get('amount')
        
        try:
            bid = place_investment_bid(request.user, listing, Decimal(amount))
            messages.success(request, f'Bid placed: {amount} ETB')
            return redirect('marketplace')
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('marketplace')


@login_required
def loan_request_view(request):
    """Submit loan request"""
    if request.user.role != 'BORROWER':
        messages.error(request, 'Only borrowers can request loans')
        return redirect('marketplace')
        
    if request.method == 'POST':
        amount = request.POST.get('amount')
        duration = request.POST.get('duration_months')
        purpose = request.POST.get('purpose')
        
        loan_request = LoanRequest.objects.create(
            borrower=request.user,
            requested_amount=Decimal(amount),
            duration_months=int(duration),
            purpose=purpose
        )
        
        # Calculate credit score immediately
        score = calculate_hybrid_credit_score(request.user)
        grade = assign_risk_grade(score)
        
        loan_request.credit_score = score
        loan_request.risk_grade = grade
        loan_request.save()
        
        messages.success(request, f'Loan request submitted with credit score: {score} (Grade: {grade})')
        return redirect('marketplace')
    
    return render(request, 'marketplace/request_loan.html')