from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

from apps.catalog.models import Author, Book, Category
from apps.dashboard.forms import OrderStatusForm, PaymentForm

from .models import Invoice, Order, OrderItem, Payment
from .stripe_services import create_checkout_session, mark_order_paid_from_checkout_session


class OrderPaymentRulesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='client',
            email='client@example.com',
            password='secret',
        )
        category = Category.objects.create(name='Architecture')
        author = Author.objects.create(first_name='Robert', last_name='Martin')
        self.book = Book.objects.create(
            title='Clean Code',
            slug='clean-code-test',
            isbn='9780132350884',
            author=author,
            category=category,
            description='Livre de test',
            price=Decimal('210.00'),
            publication_date='2008-08-01',
            publisher='Prentice Hall',
            pages=464,
            total_copies=3,
            available_copies=3,
            status='available',
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number='ORD-TEST01',
            subtotal=Decimal('210.00'),
            shipping_cost=Decimal('10.00'),
            discount=Decimal('20.00'),
            tax=Decimal('0.00'),
            total=Decimal('200.00'),
            shipping_address='Casablanca',
            status='pending',
            payment_status='pending',
        )
        OrderItem.objects.create(
            order=self.order,
            book=self.book,
            quantity=1,
            price=Decimal('210.00'),
        )

    @override_settings(
        STRIPE_SECRET_KEY='sk_test_123',
        STRIPE_PUBLISHABLE_KEY='pk_test_123',
        STRIPE_CURRENCY='mad',
    )
    def test_stripe_checkout_charges_exact_order_total(self):
        request = RequestFactory().post('/orders/1/stripe/checkout/')
        request.user = self.user

        created_session = SimpleNamespace(id='cs_test_123', url='https://stripe.test/checkout')
        stripe = SimpleNamespace(
            checkout=SimpleNamespace(
                Session=SimpleNamespace(create=Mock(return_value=created_session))
            )
        )

        with patch('apps.orders.stripe_services.get_stripe', return_value=stripe):
            session = create_checkout_session(request, self.order)

        self.assertEqual(session, created_session)
        kwargs = stripe.checkout.Session.create.call_args.kwargs
        self.assertEqual(kwargs['line_items'][0]['price_data']['unit_amount'], 20000)
        self.assertEqual(kwargs['metadata']['order_total'], '200.00')

    def test_paid_checkout_deducts_stock_once_and_creates_invoice(self):
        session = {
            'id': 'cs_test_paid',
            'payment_status': 'paid',
            'currency': 'mad',
            'payment_intent': 'pi_test_paid',
            'client_reference_id': str(self.order.id),
            'metadata': {'order_id': str(self.order.id)},
        }

        mark_order_paid_from_checkout_session(session)
        mark_order_paid_from_checkout_session(session)

        self.book.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(self.book.available_copies, 2)
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'processing')
        self.assertTrue(Invoice.objects.filter(order=self.order).exists())

    def test_admin_cannot_prepare_unpaid_order(self):
        form = OrderStatusForm(
            data={
                'status': 'processing',
                'payment_status': 'pending',
                'shipping_address': self.order.shipping_address,
                'notes': '',
            },
            instance=self.order,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_admin_payment_form_cannot_complete_unpaid_order(self):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total,
            currency='mad',
            payment_method='stripe',
            status='pending',
        )
        form = PaymentForm(
            data={
                'order': self.order.id,
                'amount': self.order.total,
                'payment_method': 'stripe',
                'status': 'completed',
                'transaction_id': 'manual',
                'completed_at': '',
            },
            instance=payment,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
