from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Borrow(models.Model):
    """Emprunt de livre."""

    STATUS_CHOICES = [
        ('pending_payment', 'Paiement en attente'),
        ('active', 'Actif'),
        ('returned', 'Retourne'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annule'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paye'),
        ('unpaid', 'Non paye'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrows')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='borrows')

    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')

    borrow_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_date = models.DateTimeField(null=True, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, db_index=True)

    is_overdue = models.BooleanField(default=False)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-borrow_date']
        verbose_name = 'Emprunt'
        verbose_name_plural = 'Emprunts'

    def __str__(self):
        return f"{self.user} - {self.book.title}"

    def is_overdue_now(self):
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date

    def get_days_left(self):
        if self.status == 'returned':
            return 0
        return (self.due_date - timezone.now().date()).days

    def get_overdue_days(self):
        if self.return_date:
            overdue_days = (self.return_date.date() - self.due_date).days
        else:
            overdue_days = (timezone.now().date() - self.due_date).days
        return max(overdue_days, 0)

    def calculate_fine(self):
        """Apres 30 jours, le prix d'emprunt est double."""
        if self.get_overdue_days() > 0:
            self.fine_amount = self.borrow_fee
            self.amount_due = self.borrow_fee * Decimal('2.00')
            self.is_overdue = True
        else:
            self.fine_amount = Decimal('0.00')
            self.amount_due = self.borrow_fee
            self.is_overdue = False
        return self.fine_amount

    @classmethod
    def calculate_borrow_fee(cls, book):
        return (book.price * Decimal('0.30')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def payment_summary(self):
        if self.fine_amount > 0:
            return f"{self.amount_due} DH (frais initial + amende)"
        return f"{self.borrow_fee} DH"


class BorrowRequest(models.Model):
    """Demande d'emprunt en attente."""

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuve'),
        ('rejected', 'Rejete'),
        ('cancelled', 'Annule'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='borrow_requests')

    requested_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests',
    )
    approval_date = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_date']
        unique_together = ['user', 'book']
        verbose_name = "Demande d'emprunt"
        verbose_name_plural = "Demandes d'emprunt"

    def __str__(self):
        return f"Demande {self.user} - {self.book.title}"
