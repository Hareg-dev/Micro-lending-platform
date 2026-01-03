from django.urls import path
from . import views
from .repayment_webhook import telebirr_repayment_webhook

urlpatterns = [
    path('webhook/telebirr/', views.telebirr_webhook, name='telebirr_webhook'),
    path('webhook/repayment/', telebirr_repayment_webhook, name='repayment_webhook'),
]