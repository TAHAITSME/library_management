from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.catalog.models import Book
from .models import Cart, CartItem


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    # ✅ Get cart items with related book data
    cart_items = cart.items.select_related('book').all()
    total = sum(item.get_total() for item in cart_items)
    return render(request, 'cart/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
        'item_count': cart_items.count(),
    })


@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if not book.is_available():
        return JsonResponse({
            'success': False,
            'message': 'Ce livre n\'est pas disponible!'
        })

    # ✅ Correction: CartItem lié via cart, pas user direct
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        book=book,
        defaults={'user': request.user, 'quantity': 1}
    )

    if not created:
        if cart_item.quantity < book.available_copies:
            cart_item.quantity += 1
            cart_item.save()
            message = f'Quantité mise à jour.'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Stock insuffisant!'
            })
    else:
        message = f'"{book.title}" ajouté au panier!'

    # Retourner JSON
    cart_items = cart.items.all()
    return JsonResponse({
        'success': True,
        'message': message,
        'book_title': book.title,
        'cart_count': cart_items.count(),
    })


@login_required
def remove_from_cart(request, book_id):
    cart = get_object_or_404(Cart, user=request.user)
    CartItem.objects.filter(cart=cart, book_id=book_id).delete()
    messages.success(request, 'Article supprimé du panier!')
    return redirect('cart:cart')


@login_required
def update_cart_item(request, book_id):
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except ValueError:
        quantity = 1

    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, book_id=book_id)

    if quantity > cart_item.book.available_copies:
        messages.warning(request, 'Stock insuffisant!')
        quantity = cart_item.book.available_copies

    cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, 'Panier mis à jour!')
    return redirect('cart:cart')


@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, 'Panier vidé!')
    return redirect('cart:cart')