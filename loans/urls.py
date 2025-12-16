from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply_loan, name='apply_loan'),
    path('dashboard/', views.loan_dashboard, name='loan_dashboard'),
    path('approve/<int:app_id>/', views.approve_loan_view, name='approve_loan'),
]