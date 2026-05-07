from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.catalog.models import Book
from apps.orders.views import calculate_order_pricing
from .models import Cart, CartItem


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('book').all()
    total = sum(item.get_total() for item in cart_items)
    pricing = calculate_order_pricing(request.user, total)

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        **pricing,
        'item_count': cart.get_item_count(),
    })


@login_required
def add_to_cart(request, book_id):
    if request.method != 'POST':
        return redirect('catalog:books_list')

    book = get_object_or_404(Book, id=book_id)
    if request.user.is_staff:
        messages.warning(request, "Les comptes administrateur ne peuvent pas ajouter des livres au panier.")
        return redirect('catalog:book_detail', slug=book.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    if not book.is_available():
        messages.error(request, "Ce livre n'est pas disponible !")
        return redirect('catalog:books_list')

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        book=book,
        defaults={'quantity': 1}
    )

    if not created:
        if cart_item.quantity < book.available_copies:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, "Quantité mise à jour.")
        else:
            messages.warning(request, "Stock insuffisant !")
    else:
        messages.success(request, f'"{book.title}" ajouté au panier !')

    return redirect('cart:cart')


@login_required
def remove_from_cart(request, book_id):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        CartItem.objects.filter(cart=cart, book_id=book_id).delete()
        messages.success(request, 'Article supprimé du panier !')

    return redirect('cart:cart')


@login_required
def update_cart_item(request, book_id):
    if request.method == 'POST':
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except ValueError:
            quantity = 1

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, book_id=book_id)

        if quantity > cart_item.book.available_copies:
            messages.warning(request, 'Stock insuffisant !')
            quantity = cart_item.book.available_copies

        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Panier mis à jour !')

    return redirect('cart:cart')


@login_required
def clear_cart(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        messages.success(request, 'Panier vidé !')

    return redirect('cart:cart')
