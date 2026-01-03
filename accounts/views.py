from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .models import User


def home_view(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        full_name = request.POST.get('full_name')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'accounts/register.html')
        
        user = User.objects.create_user(email=email, password=password, role=role)
        user.full_name = full_name
        user.save()
        
        login(request, user)
        messages.success(request, 'Account created successfully')
        return redirect('profile')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
        else:
            messages.error(request, 'Invalid credentials')
    
    form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        if user.role == 'BORROWER':
            profile = user.borrowerprofile
            profile.business_name = request.POST.get('business_name', '')
            profile.business_type = request.POST.get('business_type', '')
            profile.business_age = request.POST.get('business_age') or None
            profile.save()
            
        elif user.role == 'INVESTOR':
            profile = user.investorprofile
            profile.risk_appetite = request.POST.get('risk_appetite', 'MEDIUM')
            profile.save()
        
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'user': user})