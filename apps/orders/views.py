from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
import logging
from .models import Order, OrderItem
from apps.cart.models import Cart
from apps.catalog.models import Book

logger = logging.getLogger(__name__)


@login_required
def orders_list_view(request):
    """Afficher la liste des commandes de l'utilisateur"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book').order_by('-created_at')
    return render(request, 'orders/orders_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    """Afficher les détails d'une commande"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('book').all()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_items': order_items,
    })


@login_required
@require_http_methods(["GET", "POST"])
def create_order_view(request):
    """Créer une commande depuis le panier"""
    logger.info(f"Create order view accessed by user {request.user.id}")
    
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('book').all()

    if not cart_items.exists():
        messages.warning(request, 'Votre panier est vide!')
        return redirect('cart:cart')

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        
        if not shipping_address:
            logger.warning(f"User {request.user.id} attempted to create order without shipping address")
            messages.error(request, 'L\'adresse de livraison est requise!')
            return render(request, 'orders/create_order.html', {
                'cart_items': cart_items,
                'total': cart.get_total(),
            })

        try:
            with transaction.atomic():
                # Calculer les totaux
                subtotal = sum(item.get_total() for item in cart_items)
                total = subtotal

                # Générer un numéro de commande unique
                import uuid
                order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

                # Créer la commande
                order = Order.objects.create(
                    user=request.user,
                    order_number=order_number,
                    subtotal=subtotal,
                    shipping_cost=0,
                    tax=0,
                    total=total,
                    shipping_address=shipping_address,
                    status='pending',
                    payment_status='pending',
                )
                logger.info(f"Order {order.id} created with number {order_number}")

                # Créer les articles de commande en bulk
                order_items = [
                    OrderItem(
                        order=order,
                        book=cart_item.book,
                        quantity=cart_item.quantity,
                        price=cart_item.book.price,
                    )
                    for cart_item in cart_items
                ]
                OrderItem.objects.bulk_create(order_items)
                logger.info(f"Created {len(order_items)} order items for order {order.id}")

                # Vider le panier
                cart.clear()

                messages.success(request, f'Commande #{order.order_number} créée avec succès!')
                return redirect('orders:order_payment', order_id=order.id)
        except Exception as e:
            logger.error(f"Error creating order for user {request.user.id}: {str(e)}", exc_info=True)
            messages.error(request, f'Erreur lors de la création de la commande')
            return render(request, 'orders/create_order.html', {
                'cart_items': cart_items,
                'total': cart.get_total(),
            })

    return render(request, 'orders/create_order.html', {
        'cart_items': cart_items,
        'total': cart.get_total(),
    })


@login_required
def order_payment_view(request, order_id):
    """Processus de paiement"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Simuler le paiement (à adapter avec vrai gateway)
        payment_method = request.POST.get('payment_method')
        
        if payment_method:
            order.payment_status = 'paid'
            order.status = 'processing'
            order.save()
            
            messages.success(request, 'Paiement effectué avec succès!')
            return redirect('orders:order_detail', order_id=order.id)
        else:
            messages.error(request, 'Veuillez sélectionner un mode de paiement.')

    return render(request, 'orders/order_payment.html', {'order': order})