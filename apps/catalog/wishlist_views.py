"""Vues pour la gestion de la wishlist"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from apps.catalog.models import Book, Wishlist, WishlistItem
import logging

logger = logging.getLogger(__name__)


@login_required
def wishlist_view(request):
    """Afficher la liste de souhaits de l'utilisateur"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist.items.select_related('book').all()
    
    context = {
        'wishlist': wishlist,
        'items': items,
        'total_items': items.count(),
        'total_value': sum(item.book.price for item in items),
    }
    return render(request, 'catalog/wishlist.html', context)


@login_required
@require_POST
def add_to_wishlist(request, book_id):
    """Ajouter un livre à la wishlist"""
    try:
        book = get_object_or_404(Book, id=book_id)
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        
        # Get priority from POST data
        priority = int(request.POST.get('priority', 0))
        
        item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            book=book,
            defaults={'priority': priority}
        )
        
        if not created:
            # Update priority if item already exists
            item.priority = priority
            item.save()
            message = f"{book.title} est déjà dans votre wishlist. Priorité mise à jour."
        else:
            message = f"{book.title} a été ajouté à votre wishlist."
        
        logger.info(f"User {request.user} added {book.title} to wishlist")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'wishlist_count': wishlist.get_item_count(),
            })
        
        return redirect('catalog:book_detail', book_id=book_id)
    
    except Exception as e:
        logger.error(f"Error adding to wishlist: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Erreur lors de l\'ajout'}, status=400)
        return redirect('catalog:books_list')


@login_required
@require_POST
def remove_from_wishlist(request, item_id):
    """Supprimer un livre de la wishlist"""
    try:
        item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
        book_title = item.book.title
        item.delete()
        
        logger.info(f"User {request.user} removed {book_title} from wishlist")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{book_title} a été retiré de votre wishlist.'
            })
        
        return redirect('catalog:wishlist')
    
    except Exception as e:
        logger.error(f"Error removing from wishlist: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Erreur lors de la suppression'}, status=400)
        return redirect('catalog:wishlist')


@login_required
@require_POST
def update_wishlist_priority(request, item_id):
    """Mettre à jour la priorité d'un article de la wishlist"""
    try:
        item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
        priority = int(request.POST.get('priority', 0))
        
        if 0 <= priority <= 2:
            item.priority = priority
            item.save()
            logger.info(f"User {request.user} updated priority for {item.book.title}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Priorité mise à jour'})
        
        return redirect('catalog:wishlist')
    
    except Exception as e:
        logger.error(f"Error updating priority: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Erreur lors de la mise à jour'}, status=400)
        return redirect('catalog:wishlist')


@login_required
@require_GET
def wishlist_api(request):
    """API JSON pour récupérer la wishlist (pour AJAX)"""
    try:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        items = wishlist.items.select_related('book').values(
            'id',
            'book__id',
            'book__title',
            'book__price',
            'priority',
            'added_at'
        )
        
        return JsonResponse({
            'success': True,
            'count': wishlist.get_item_count(),
            'total_value': float(sum(item['book__price'] for item in items)),
            'items': list(items),
        })
    
    except Exception as e:
        logger.error(f"Error fetching wishlist: {e}")
        return JsonResponse({'success': False, 'message': 'Erreur'}, status=400)
