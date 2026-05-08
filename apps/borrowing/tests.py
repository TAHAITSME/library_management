from decimal import Decimal
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Author, Book, Category

from .models import Borrow


class BorrowBusinessRulesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='borrower',
            email='borrower@example.com',
            password='secret',
        )
        category = Category.objects.create(name='Software')
        author = Author.objects.create(first_name='Robert', last_name='Martin')
        self.book = Book.objects.create(
            title='Clean Code Borrow',
            slug='clean-code-borrow',
            isbn='9780132350885',
            author=author,
            category=category,
            description='Livre de test',
            price=Decimal('210.00'),
            publication_date='2008-08-01',
            publisher='Prentice Hall',
            pages=464,
            total_copies=2,
            available_copies=2,
            status='available',
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_borrow_confirmation_redirects_to_stripe_without_decrementing_stock(self):
        created_session = SimpleNamespace(id='cs_borrow_test', url='https://stripe.test/borrow')
        stripe = SimpleNamespace(
            checkout=SimpleNamespace(
                Session=SimpleNamespace(create=Mock(return_value=created_session))
            )
        )

        with patch('apps.borrowing.stripe_services.get_stripe', return_value=stripe):
            response = self.client.post(reverse('borrowing:borrow_request', args=[self.book.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, created_session.url)
        borrow = Borrow.objects.get(user=self.user, book=self.book)
        self.book.refresh_from_db()

        self.assertEqual(borrow.borrow_fee, Decimal('63.00'))
        self.assertEqual(borrow.amount_due, Decimal('63.00'))
        self.assertEqual(borrow.status, 'pending_payment')
        self.assertEqual(borrow.payment_status, 'unpaid')
        self.assertEqual(self.book.available_copies, 2)

    def test_paid_stripe_session_activates_borrow_and_decrements_stock(self):
        from .stripe_services import mark_borrow_paid_from_checkout_session

        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now().date() + timedelta(days=30),
            status='pending_payment',
            borrow_fee=Decimal('63.00'),
            amount_due=Decimal('63.00'),
            payment_status='unpaid',
        )

        mark_borrow_paid_from_checkout_session({
            'id': 'cs_borrow_paid',
            'payment_status': 'paid',
            'client_reference_id': str(borrow.id),
            'metadata': {'borrow_id': str(borrow.id)},
        })

        borrow.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(borrow.status, 'active')
        self.assertEqual(borrow.payment_status, 'paid')
        self.assertEqual(self.book.available_copies, 1)

    def test_late_borrow_doubles_borrow_cost(self):
        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now().date() - timedelta(days=1),
            status='active',
            borrow_fee=Decimal('63.00'),
            amount_due=Decimal('63.00'),
            payment_status='paid',
            payment_date=timezone.now(),
        )

        borrow.calculate_fine()

        self.assertEqual(borrow.fine_amount, Decimal('63.00'))
        self.assertEqual(borrow.amount_due, Decimal('126.00'))
        self.assertTrue(borrow.is_overdue)

    def test_return_increases_stock_once(self):
        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now().date() + timedelta(days=10),
            status='active',
            borrow_fee=Decimal('63.00'),
            amount_due=Decimal('63.00'),
            payment_status='paid',
            payment_date=timezone.now(),
        )
        self.book.available_copies = 1
        self.book.save(update_fields=['available_copies'])

        response = self.client.post(reverse('borrowing:return_book', args=[borrow.id]))
        self.assertEqual(response.status_code, 302)
        self.book.refresh_from_db()
        borrow.refresh_from_db()

        self.assertEqual(borrow.status, 'returned')
        self.assertEqual(self.book.available_copies, 2)
