import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.cart.models import Cart

from .models import Order, OrderItem, Payment
from .stripe_services import (
    create_checkout_session,
    get_stripe,
    mark_order_paid_from_checkout_session,
    mark_order_payment_failed_from_checkout_session,
)

logger = logging.getLogger(__name__)


@staff_member_required
def payments_admin_list_view(request):
    payments = Payment.objects.select_related('order', 'order__user').order_by('-created_at')
    return render(request, 'orders/payments_admin_list.html', {'payments': payments})


@login_required
def orders_list_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book').order_by('-created_at')
    return render(request, 'orders/orders_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('book').all()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_items': order_items,
    })


@login_required
@require_http_methods(["GET", "POST"])
def create_order_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('book').all()

    if not cart_items.exists():
        messages.warning(request, 'Votre panier est vide.')
        return redirect('cart:cart')

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        if not shipping_address:
            messages.error(request, "L'adresse de livraison est requise.")
            return render(request, 'orders/create_order.html', {
                'cart_items': cart_items,
                'total': cart.get_total(),
            })

        try:
            with transaction.atomic():
                subtotal = sum(item.get_total() for item in cart_items)
                order = Order.objects.create(
                    user=request.user,
                    order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                    subtotal=subtotal,
                    shipping_cost=0,
                    tax=0,
                    total=subtotal,
                    shipping_address=shipping_address,
                    status='pending',
                    payment_status='pending',
                )

                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        book=cart_item.book,
                        quantity=cart_item.quantity,
                        price=cart_item.book.price,
                    )
                    for cart_item in cart_items
                ])
                cart.clear()

            messages.success(request, f'Commande #{order.order_number} creee avec succes.')
            return redirect('orders:order_payment', order_id=order.id)
        except Exception as exc:
            logger.exception('Erreur creation commande pour user %s', request.user.id)
            messages.error(request, f'Erreur lors de la creation de la commande: {exc}')

    return render(request, 'orders/create_order.html', {
        'cart_items': cart_items,
        'total': cart.get_total(),
    })


@login_required
def order_payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == 'paid':
        messages.info(request, 'Cette commande est deja payee.')
        return redirect('orders:order_detail', order_id=order.id)

    return render(request, 'orders/order_payment.html', {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
@require_http_methods(["POST"])
def create_stripe_checkout_session_view(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__book'),
        id=order_id,
        user=request.user,
    )

    if order.payment_status == 'paid':
        messages.info(request, 'Cette commande est deja payee.')
        return redirect('orders:order_detail', order_id=order.id)

    if not order.items.exists():
        messages.error(request, 'Impossible de payer une commande vide.')
        return redirect('orders:order_detail', order_id=order.id)

    try:
        session = create_checkout_session(request, order)
    except Exception as exc:
        logger.exception('Erreur creation session Stripe pour commande %s', order.id)
        messages.error(request, f'Erreur Stripe: {exc}')
        return redirect('orders:order_payment', order_id=order.id)

    return redirect(session.url)


@login_required
def stripe_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/payment_success.html', {'order': order})


@login_required
def stripe_cancel_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/payment_cancel.html', {'order': order})


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook_view(request):
    stripe = get_stripe()
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    event_type = event.get('type')
    session = event['data']['object']

    if event_type == 'checkout.session.completed':
        if session.get('payment_status') == 'paid':
            mark_order_paid_from_checkout_session(session)
    elif event_type in ('checkout.session.expired', 'payment_intent.payment_failed'):
        mark_order_payment_failed_from_checkout_session(session)

    return HttpResponse(status=200)
