from decimal import Decimal
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Book

from .models import Invoice, Order, Payment


def disable_broken_local_proxy():
    """Evite qu'un proxy local invalide bloque les appels Stripe en dev."""
    proxy_keys = ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy')
    for key in proxy_keys:
        value = os.environ.get(key, '')
        if '127.0.0.1:9' in value or 'localhost:9' in value:
            os.environ.pop(key, None)


def get_stripe():
    disable_broken_local_proxy()
    try:
        import stripe
    except ImportError as exc:
        raise ImproperlyConfigured('Installez le package stripe: pip install stripe') from exc

    if not settings.STRIPE_SECRET_KEY:
        raise ImproperlyConfigured('STRIPE_SECRET_KEY est manquant dans .env')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def money_to_minor_units(amount):
    return int((Decimal(amount) * 100).quantize(Decimal('1')))


def create_checkout_session(request, order):
    stripe = get_stripe()
    item_count = sum(item.quantity for item in order.items.all())
    description_parts = [
        f'{item.book.title} x{item.quantity}'
        for item in order.items.select_related('book')
    ]
    description_parts.append(f'Livraison: {order.shipping_cost} DH')
    if order.discount:
        description_parts.append(f'Remise: -{order.discount} DH')

    line_items = [{
        'price_data': {
            'currency': settings.STRIPE_CURRENCY,
            'product_data': {
                'name': f'Commande {order.order_number}',
                'description': ' | '.join(description_parts)[:1000],
            },
            'unit_amount': money_to_minor_units(order.total),
        },
        'quantity': 1,
    }]

    success_url = request.build_absolute_uri(
        reverse('orders:stripe_success', kwargs={'order_id': order.id})
    ) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(
        reverse('orders:stripe_cancel', kwargs={'order_id': order.id})
    )

    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        line_items=line_items,
        customer_email=order.user.email or None,
        client_reference_id=str(order.id),
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'order_id': str(order.id),
            'user_id': str(order.user_id),
            'order_number': order.order_number,
            'order_total': str(order.total),
            'item_count': str(item_count),
        },
        payment_intent_data={
            'metadata': {
                'order_id': str(order.id),
                'user_id': str(order.user_id),
                'order_number': order.order_number,
                'order_total': str(order.total),
            },
        },
    )

    order.stripe_checkout_session_id = session.id
    if order.payment_status == 'failed':
        order.payment_status = 'pending'
        order.save(update_fields=['stripe_checkout_session_id', 'payment_status', 'updated_at'])
    else:
        order.save(update_fields=['stripe_checkout_session_id', 'updated_at'])

    Payment.objects.update_or_create(
        order=order,
        defaults={
            'amount': order.total,
            'currency': settings.STRIPE_CURRENCY,
            'payment_method': 'stripe',
            'status': 'pending',
            'stripe_checkout_session_id': session.id,
        },
    )

    return session


def confirm_checkout_session(session_id, expected_order_id=None):
    stripe = get_stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    metadata = session.get('metadata') or {}
    order_id = metadata.get('order_id') or session.get('client_reference_id')
    if expected_order_id is not None and str(order_id) != str(expected_order_id):
        raise ValueError('La session Stripe ne correspond pas a cette commande.')
    if session.get('payment_status') == 'paid':
        return mark_order_paid_from_checkout_session(session)
    return None


@transaction.atomic
def mark_order_paid_from_checkout_session(session):
    metadata = session.get('metadata') or {}
    order_id = metadata.get('order_id') or session.get('client_reference_id')
    if not order_id:
        return None

    order = (
        Order.objects.select_for_update()
        .select_related('user')
        .prefetch_related('items__book')
        .get(id=order_id)
    )

    already_paid = order.payment_status == 'paid'
    paid_at = timezone.now()
    payment_intent_id = session.get('payment_intent') or ''

    Payment.objects.update_or_create(
        order=order,
        defaults={
            'amount': order.total,
            'currency': (session.get('currency') or settings.STRIPE_CURRENCY).lower(),
            'payment_method': 'stripe',
            'status': 'completed',
            'transaction_id': payment_intent_id,
            'stripe_checkout_session_id': session.get('id', ''),
            'stripe_payment_intent_id': payment_intent_id,
            'paid_at': paid_at,
            'completed_at': paid_at,
        },
    )

    if not already_paid:
        for item in order.items.select_for_update().select_related('book'):
            book = Book.objects.select_for_update().get(pk=item.book_id)
            if book.available_copies < item.quantity:
                raise ValueError(
                    f"Stock insuffisant pour {book.title}: "
                    f"{book.available_copies} disponible(s), {item.quantity} demande(s)."
                )
            book.available_copies -= item.quantity
            book.status = 'available' if book.available_copies > 0 else 'unavailable'
            book.save(update_fields=['available_copies', 'status', 'updated_at'])

    order.payment_status = 'paid'
    if order.status == 'pending':
        order.status = 'processing'
    order.stripe_checkout_session_id = session.get('id', order.stripe_checkout_session_id)
    order.save(update_fields=['payment_status', 'status', 'stripe_checkout_session_id', 'updated_at'])

    Invoice.objects.get_or_create(
        order=order,
        defaults={
            'invoice_number': Invoice().generate_invoice_number(),
            'billing_address': order.shipping_address,
            'notes': 'Facture generee automatiquement apres paiement Stripe.',
        },
    )

    return order


@transaction.atomic
def mark_order_payment_failed_from_checkout_session(session):
    metadata = session.get('metadata') or {}
    order_id = metadata.get('order_id') or session.get('client_reference_id')
    if not order_id:
        return None

    order = Order.objects.select_for_update().get(id=order_id)
    if order.payment_status != 'paid' and order.status != 'cancelled':
        order.payment_status = 'failed'
        order.save(update_fields=['payment_status', 'updated_at'])

    Payment.objects.update_or_create(
        order=order,
        defaults={
            'amount': order.total,
            'currency': (session.get('currency') or settings.STRIPE_CURRENCY).lower(),
            'payment_method': 'stripe',
            'status': 'failed',
            'stripe_checkout_session_id': session.get('id', ''),
            'stripe_payment_intent_id': session.get('payment_intent') or '',
        },
    )
    return order
