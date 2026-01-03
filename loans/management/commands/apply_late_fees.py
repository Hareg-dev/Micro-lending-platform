from django.core.management.base import BaseCommand
from loans.repayment_engine import apply_late_fees


class Command(BaseCommand):
    help = 'Apply late fees to overdue repayments'

    def handle(self, *args, **options):
        apply_late_fees()
        self.stdout.write(
            self.style.SUCCESS('Successfully applied late fees')
        )