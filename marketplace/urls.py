from django.urls import path
from . import views

urlpatterns = [
    path('', views.marketplace_view, name='marketplace'),
    path('request/', views.loan_request_view, name='loan_request'),
    path('bid/<int:listing_id>/', views.place_bid_view, name='place_bid'),
]