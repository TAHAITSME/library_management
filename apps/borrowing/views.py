import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.catalog.models import Book

from .models import Borrow, BorrowRequest
from .stripe_services import confirm_borrow_checkout_session, create_borrow_checkout_session
from .stripe_services import mark_borrow_paid_from_checkout_session

logger = logging.getLogger(__name__)


def refresh_borrow_financial_state(borrow):
    if borrow.status == 'pending_payment':
        return
    if borrow.due_date < timezone.now().date() and borrow.status == 'active':
        borrow.status = 'overdue'
    borrow.calculate_fine()
    borrow.save(update_fields=['status', 'is_overdue', 'fine_amount', 'amount_due'])


@login_required
def borrow_list_view(request):
    active_borrows = Borrow.objects.filter(
        user=request.user,
        status__in=['active', 'overdue'],
    ).select_related('book').order_by('due_date')

    for borrow in active_borrows:
        refresh_borrow_financial_state(borrow)

    active_borrows = Borrow.objects.filter(
        user=request.user,
        status__in=['active', 'overdue'],
    ).select_related('book').order_by('due_date')

    returned_borrows = Borrow.objects.filter(
        user=request.user,
        status='returned',
    ).select_related('book').order_by('-return_date')[:10]

    stats = {
        'total_active': active_borrows.count(),
        'overdue_count': active_borrows.filter(status='overdue').count(),
        'total_fine': sum(b.fine_amount for b in active_borrows.filter(status='overdue')),
        'total_due': sum(b.amount_due for b in active_borrows),
    }

    return render(request, 'borrowing/borrow_list.html', {
        'active_borrows': active_borrows,
        'returned_borrows': returned_borrows,
        'stats': stats,
    })


@login_required
def borrow_detail_view(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)
    refresh_borrow_financial_state(borrow)

    days_left = borrow.get_days_left()
    is_overdue = borrow.is_overdue_now()

    return render(request, 'borrowing/borrow_detail.html', {
        'borrow': borrow,
        'days_left': days_left,
        'is_overdue': is_overdue,
        'can_renew': borrow.status == 'active' and not is_overdue and 0 < days_left <= 7,
        'can_return': borrow.status in ['active', 'overdue'],
    })


@login_required
def borrow_request_legacy_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.user.is_staff:
        messages.warning(request, "Les comptes administrateur ne peuvent pas demander un emprunt.")
        return redirect('catalog:book_detail', slug=book.slug)

    existing_request = BorrowRequest.objects.filter(user=request.user, book=book, status='pending').exists()
    if existing_request:
        messages.warning(request, "Une demande d'emprunt est deja en attente pour ce livre.")
        return redirect('catalog:book_detail', slug=book.slug)

    existing_borrow = Borrow.objects.filter(
        user=request.user,
        book=book,
        status__in=['pending_payment', 'active', 'overdue'],
    ).exists()
    if existing_borrow:
        messages.warning(request, 'Vous avez deja emprunte ce livre.')
        return redirect('catalog:book_detail', slug=book.slug)

    borrow_request, created = BorrowRequest.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={'status': 'pending'},
    )

    if created:
        messages.success(request, "Demande d'emprunt creee avec succes.")
    else:
        messages.info(request, 'Vous avez deja une demande pour ce livre.')

    return redirect('borrowing:borrow_list')


@login_required
@require_http_methods(["GET", "POST"])
def return_book_view(request, borrow_id):
    borrow = get_object_or_404(Borrow.objects.select_related('book'), id=borrow_id, user=request.user)

    if borrow.status == 'returned':
        messages.warning(request, 'Ce livre a deja ete retourne.')
        return redirect('borrowing:borrow_list')

    refresh_borrow_financial_state(borrow)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                borrow = Borrow.objects.select_for_update().select_related('book').get(id=borrow.id)
                borrow.return_date = timezone.now()
                borrow.status = 'returned'
                borrow.calculate_fine()
                borrow.save(update_fields=['return_date', 'status', 'is_overdue', 'fine_amount', 'amount_due'])

                book = Book.objects.select_for_update().get(pk=borrow.book_id)
                book.available_copies = min(book.total_copies, book.available_copies + 1)
                book.status = 'available' if book.available_copies > 0 else 'unavailable'
                book.save(update_fields=['available_copies', 'status', 'updated_at'])

                messages.success(request, 'Livre retourne avec succes.')
                if borrow.fine_amount > 0:
                    messages.warning(
                        request,
                        f'Amende de {borrow.fine_amount} DH appliquee: le cout total devient {borrow.amount_due} DH.',
                    )
        except Exception:
            logger.exception('Erreur retour emprunt %s', borrow_id)
            messages.error(request, 'Erreur lors du retour du livre.')

        return redirect('borrowing:borrow_list')

    return render(request, 'borrowing/confirm_return.html', {'borrow': borrow})


@login_required
def renew_borrow_view(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id, user=request.user)

    if borrow.status == 'returned':
        messages.warning(request, 'Ce livre a deja ete retourne.')
        return redirect('borrowing:borrow_list')

    if borrow.is_overdue_now():
        messages.error(request, 'Vous ne pouvez pas renouveler un emprunt en retard.')
        return redirect('borrowing:borrow_list')

    days_left = borrow.get_days_left()
    if days_left > 7:
        messages.warning(request, 'Le renouvellement est disponible seulement dans les 7 derniers jours.')
        return redirect('borrowing:borrow_list')

    borrow.due_date += timedelta(days=30)
    borrow.save(update_fields=['due_date'])

    messages.success(request, f'Emprunt renouvele. Nouvelle date: {borrow.due_date.strftime("%d/%m/%Y")}.')
    return redirect('borrowing:borrow_detail', borrow_id=borrow_id)


@login_required
@require_http_methods(["GET", "POST"])
def borrow_direct_view(request, book_id):
    if request.user.is_staff:
        messages.warning(request, "Les comptes administrateur ne peuvent pas demander un emprunt.")
        return redirect('catalog:books_list')

    book = get_object_or_404(Book, id=book_id)
    borrow_fee = Borrow.calculate_borrow_fee(book)
    due_date = timezone.now().date() + timedelta(days=30)

    pending_borrow = Borrow.objects.filter(
        user=request.user,
        book=book,
        status='pending_payment',
        payment_status='unpaid',
    ).first()
    active_borrow_exists = Borrow.objects.filter(
        user=request.user,
        book=book,
        status__in=['active', 'overdue'],
    ).exists()
    if active_borrow_exists:
        messages.warning(request, 'Vous avez deja un emprunt actif pour ce livre.')
        return redirect('catalog:book_detail', slug=book.slug)

    if not book.is_available():
        messages.error(request, "Ce livre n'est pas disponible pour l'emprunt.")
        return redirect('catalog:book_detail', slug=book.slug)

    if request.method == 'GET':
        return render(request, 'borrowing/borrow_checkout.html', {
            'book': book,
            'borrow_fee': pending_borrow.borrow_fee if pending_borrow else borrow_fee,
            'late_fee': pending_borrow.borrow_fee if pending_borrow else borrow_fee,
            'late_total': (pending_borrow.borrow_fee if pending_borrow else borrow_fee) * 2,
            'due_date': pending_borrow.due_date if pending_borrow else due_date,
        })

    try:
        with transaction.atomic():
            book = Book.objects.select_for_update().get(id=book_id)

            if not book.is_available():
                messages.error(request, "Ce livre n'est plus disponible pour l'emprunt.")
                return redirect('catalog:book_detail', slug=book.slug)

            if pending_borrow:
                borrow = Borrow.objects.select_for_update().get(pk=pending_borrow.pk)
            else:
                borrow_fee = Borrow.calculate_borrow_fee(book)
                borrow = Borrow.objects.create(
                    user=request.user,
                    book=book,
                    due_date=due_date,
                    status='pending_payment',
                    borrow_fee=borrow_fee,
                    amount_due=borrow_fee,
                    payment_status='unpaid',
                )

            BorrowRequest.objects.filter(
                user=request.user,
                book=book,
                status='pending',
            ).update(
                status='approved',
                approved_by=request.user,
                approval_date=timezone.now(),
            )

        session = create_borrow_checkout_session(request, borrow)
        return redirect(session.url)
    except Book.DoesNotExist:
        messages.error(request, 'Livre introuvable.')
        return redirect('catalog:books_list')
    except Exception as exc:
        logger.exception('Erreur creation paiement emprunt livre %s', book_id)
        messages.error(request, f'Erreur Stripe: {exc}')
        return redirect('catalog:book_detail', slug=book.slug)


@login_required
def stripe_success_view(request, borrow_id):
    borrow = get_object_or_404(Borrow.objects.select_related('book'), id=borrow_id, user=request.user)
    session_id = request.GET.get('session_id')

    if borrow.payment_status != 'paid' and session_id:
        try:
            borrow = confirm_borrow_checkout_session(session_id, expected_borrow_id=borrow.id) or borrow
            if borrow.payment_status != 'paid':
                messages.warning(request, 'Paiement en cours de confirmation. Merci de patienter quelques instants.')
                return redirect('catalog:book_detail', slug=borrow.book.slug)
            messages.success(request, f'Paiement confirme. Emprunt actif jusqu au {borrow.due_date.strftime("%d/%m/%Y")}.')
        except Exception:
            logger.exception('Erreur confirmation Stripe emprunt %s', borrow.id)
            if settings.DEBUG:
                try:
                    borrow = mark_borrow_paid_from_checkout_session({
                        'id': session_id,
                        'payment_status': 'paid',
                        'client_reference_id': str(borrow.id),
                        'metadata': {
                            'borrow_id': str(borrow.id),
                            'book_id': str(borrow.book_id),
                            'user_id': str(borrow.user_id),
                        },
                    })
                    messages.success(request, f'Paiement valide en mode developpement. Emprunt actif jusqu au {borrow.due_date.strftime("%d/%m/%Y")}.')
                    return redirect('borrowing:borrow_detail', borrow_id=borrow.id)
                except Exception:
                    logger.exception('Erreur fallback dev emprunt %s', borrow.id)
            messages.error(request, "Paiement non confirme: le livre n'a pas ete reserve.")
            return redirect('catalog:book_detail', slug=borrow.book.slug)

    return redirect('borrowing:borrow_detail', borrow_id=borrow.id)


@login_required
def stripe_cancel_view(request, borrow_id):
    borrow = get_object_or_404(Borrow.objects.select_related('book'), id=borrow_id, user=request.user)
    if borrow.payment_status != 'paid':
        borrow.status = 'cancelled'
        borrow.save(update_fields=['status'])
    messages.warning(request, "Paiement annule. Aucun exemplaire n'a ete reserve.")
    return redirect('catalog:book_detail', slug=borrow.book.slug)
