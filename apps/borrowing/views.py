from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from datetime import timedelta
import logging
from .models import Borrow, BorrowRequest
from apps.catalog.models import Book

logger = logging.getLogger(__name__)


@login_required
def borrow_list_view(request):
    """Liste des emprunts de l'utilisateur"""
    # Emprunts actifs
    active_borrows = Borrow.objects.filter(
        user=request.user, status__in=['active', 'overdue']
    ).select_related('book').order_by('due_date')
    
    # Mettre à jour le statut overdue pour les emprunts en retard
    today = timezone.now().date()
    for borrow in active_borrows:
        if borrow.due_date < today and borrow.status == 'active':
            borrow.is_overdue = True
            borrow.status = 'overdue'
            borrow.calculate_fine()
            borrow.save()
    
    # Récharger après mise à jour
    active_borrows = Borrow.objects.filter(
        user=request.user, status__in=['active', 'overdue']
    ).select_related('book').order_by('due_date')
    
    # Emprunts retournés
    returned_borrows = Borrow.objects.filter(
        user=request.user, status='returned'
    ).select_related('book').order_by('-return_date')[:10]
    
    # Statistiques
    stats = {
        'total_active': active_borrows.count(),
        'overdue_count': active_borrows.filter(status='overdue').count(),
        'total_fine': sum(b.fine_amount for b in active_borrows.filter(status='overdue')),
    }
    
    context = {
        'active_borrows': active_borrows,
        'returned_borrows': returned_borrows,
        'stats': stats,
    }
    return render(request, 'borrowing/borrow_list.html', context)


@login_required
def borrow_detail_view(request, borrow_id):
    """Détail d'un emprunt"""
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    
    days_left = borrow.get_days_left()
    is_overdue = borrow.is_overdue_now()
    
    context = {
        'borrow': borrow,
        'days_left': days_left,
        'is_overdue': is_overdue,
        'can_renew': borrow.status == 'active' and not is_overdue and days_left > 0 and days_left <= 7,
        'can_return': borrow.status in ['active', 'overdue'],
    }
    return render(request, 'borrowing/borrow_detail.html', context)


@login_required
def borrow_request_view(request, book_id):
    """Demander un emprunt"""
    book = get_object_or_404(Book, id=book_id)
    
    # Vérifier si une demande existe déjà
    existing_request = BorrowRequest.objects.filter(user=request.user, book=book, status='pending').exists()
    if existing_request:
        messages.warning(request, 'Une demande d\'emprunt est déjà en attente pour ce livre!')
        return redirect('catalog:book_detail', slug=book.slug)
    
    # Vérifier si l'utilisateur a déjà emprunté ce livre
    existing_borrow = Borrow.objects.filter(user=request.user, book=book, status='active').exists()
    if existing_borrow:
        messages.warning(request, 'Vous avez déjà emprunté ce livre!')
        return redirect('catalog:book_detail', slug=book.slug)
    
    borrow_request, created = BorrowRequest.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={'status': 'pending'}
    )
    
    if created:
        messages.success(request, 'Demande d\'emprunt créée avec succès!')
    else:
        messages.info(request, 'Vous avez déjà une demande pour ce livre.')
    
    return redirect('borrowing:borrow_list')


@login_required
def return_book_view(request, borrow_id):
    """Retourner un livre emprunté"""
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    
    if borrow.status == 'returned':
        messages.warning(request, 'Ce livre a déjà été retourné!')
        return redirect('borrowing:borrow_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mettre à jour l'emprunt
                borrow.return_date = timezone.now()
                borrow.status = 'returned'
                borrow.calculate_fine()
                borrow.save()
                logger.info(f"Borrow {borrow.id} marked as returned for user {request.user.id}")
                
                # Augmenter le nombre de copies disponibles
                borrow.book.available_copies += 1
                borrow.book.save()
                logger.info(f"Book {borrow.book.id} available copies increased to {borrow.book.available_copies}")
                
                messages.success(request, '✓ Livre retourné avec succès!')
                
                if borrow.fine_amount > 0:
                    messages.warning(request, f'⚠️ Pénalité de {borrow.fine_amount}€ pour retard enregistrée.')
        except Exception as e:
            logger.error(f"Error returning book borrow {borrow_id}: {str(e)}", exc_info=True)
            messages.error(request, 'Erreur lors du retour du livre!')
        
        return redirect('borrowing:borrow_list')
    
    context = {'borrow': borrow}
    return render(request, 'borrowing/confirm_return.html', context)


@login_required
def renew_borrow_view(request, borrow_id):
    """Renouveler un emprunt"""
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    
    if borrow.status == 'returned':
        messages.warning(request, 'Ce livre a déjà été retourné!')
        return redirect('borrowing:borrow_list')
    
    if borrow.is_overdue_now():
        messages.error(request, 'Vous ne pouvez pas renouveler un emprunt en retard!')
        return redirect('borrowing:borrow_list')
    
    days_left = borrow.get_days_left()
    if days_left > 7:
        messages.warning(request, 'Vous pouvez renouveler un emprunt seulement 7 jours avant sa date limite.')
        return redirect('borrowing:borrow_list')
    
    # Renouveler pour 30 jours supplémentaires
    old_due = borrow.due_date
    borrow.due_date += timedelta(days=30)
    borrow.save()
    
    messages.success(request, f'✓ Emprunt renouvelé! Nouvelle date: {borrow.due_date.strftime("%d %b %Y")}')
    return redirect('borrowing:borrow_detail', borrow_id=borrow_id)
