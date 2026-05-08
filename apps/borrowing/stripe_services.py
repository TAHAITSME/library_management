from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Book
from apps.orders.stripe_services import get_stripe, money_to_minor_units

from .models import Borrow


def create_borrow_checkout_session(request, borrow):
    stripe = get_stripe()
    success_url = request.build_absolute_uri(
        reverse('borrowing:stripe_success', kwargs={'borrow_id': borrow.id})
    ) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(
        reverse('borrowing:stripe_cancel', kwargs={'borrow_id': borrow.id})
    )

    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        customer_email=borrow.user.email or None,
        client_reference_id=str(borrow.id),
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{
            'price_data': {
                'currency': settings.STRIPE_CURRENCY,
                'product_data': {
                    'name': f'Emprunt - {borrow.book.title}',
                    'description': f'Frais emprunt 30% pour 30 jours. Retard: total double a {borrow.borrow_fee * 2} DH.',
                },
                'unit_amount': money_to_minor_units(borrow.borrow_fee),
            },
            'quantity': 1,
        }],
        metadata={
            'borrow_id': str(borrow.id),
            'book_id': str(borrow.book_id),
            'user_id': str(borrow.user_id),
            'borrow_fee': str(borrow.borrow_fee),
        },
        payment_intent_data={
            'metadata': {
                'borrow_id': str(borrow.id),
                'book_id': str(borrow.book_id),
                'user_id': str(borrow.user_id),
            },
        },
    )

    borrow.stripe_checkout_session_id = session.id
    borrow.save(update_fields=['stripe_checkout_session_id'])
    return session


def confirm_borrow_checkout_session(session_id, expected_borrow_id=None):
    stripe = get_stripe()
    session = stripe.checkout.Session.retrieve(
        session_id,
        expand=['payment_intent'],
    )
    borrow_id = (session.get('metadata') or {}).get('borrow_id') or session.get('client_reference_id')
    if expected_borrow_id is not None and str(borrow_id) != str(expected_borrow_id):
        raise ValueError("La session Stripe ne correspond pas a cet emprunt.")
    payment_intent = session.get('payment_intent')
    payment_intent_status = payment_intent.get('status') if hasattr(payment_intent, 'get') else ''
    if session.get('payment_status') == 'paid' or payment_intent_status == 'succeeded':
        return mark_borrow_paid_from_checkout_session(session)
    return None


@transaction.atomic
def mark_borrow_paid_from_checkout_session(session):
    borrow_id = (session.get('metadata') or {}).get('borrow_id') or session.get('client_reference_id')
    if not borrow_id:
        return None

    borrow = (
        Borrow.objects.select_for_update()
        .select_related('book', 'user')
        .get(id=borrow_id)
    )

    if borrow.payment_status == 'paid':
        return borrow

    book = Book.objects.select_for_update().get(pk=borrow.book_id)
    if not book.is_available():
        raise ValueError("Ce livre n'est plus disponible pour l'emprunt.")

    book.available_copies -= 1
    book.status = 'available' if book.available_copies > 0 else 'unavailable'
    book.save(update_fields=['available_copies', 'status', 'updated_at'])

    borrow.status = 'active'
    borrow.payment_status = 'paid'
    borrow.payment_date = timezone.now()
    borrow.due_date = timezone.now().date() + timedelta(days=30)
    borrow.amount_due = borrow.borrow_fee
    borrow.stripe_checkout_session_id = session.get('id', borrow.stripe_checkout_session_id)
    borrow.save(update_fields=[
        'status', 'payment_status', 'payment_date', 'due_date',
        'amount_due', 'stripe_checkout_session_id',
    ])
    return borrow
