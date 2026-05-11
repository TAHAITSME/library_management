from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from .models import Reservation, ReservationQueue, ReservationNotification
from apps.catalog.models import Book
from apps.accounts.utils import notification_url, notify_user


def create_reservation_notification(reservation, notification_type, message):
    ReservationNotification.objects.create(
        reservation=reservation,
        notification_type=notification_type,
        message=message,
        is_sent=True,
        sent_at=timezone.now(),
    )
    notify_user(
        reservation.user,
        'Reservation',
        message,
        'reservation',
        notification_url('reservations:detail', pk=reservation.pk),
    )


def refresh_queue_and_notify_next(book):
    try:
        queue = ReservationQueue.objects.get(book=book)
    except ReservationQueue.DoesNotExist:
        return

    queue.total_reservations = Reservation.objects.filter(book=book, status='active').count()
    queue.save(update_fields=['total_reservations'])
    queue.update_queue_positions()

    next_reservation = queue.get_next_reservation()
    if next_reservation and next_reservation.is_ready_for_pickup():
        message = f'"{book.title}" est disponible. Vous pouvez le recuperer avant expiration.'
        if not next_reservation.notifications.filter(notification_type='ready_for_pickup').exists():
            create_reservation_notification(next_reservation, 'ready_for_pickup', message)


@login_required
def reservation_list(request):
    reservations = Reservation.objects.filter(
        user=request.user
    ).select_related('book').order_by('-reservation_date')

    context = {
        'reservations': reservations,
        'active_reservations': reservations.filter(status='active').count(),
        'completed_reservations': reservations.filter(status='completed').count(),
    }
    return render(request, 'reservations/list.html', context)


@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    notifications = reservation.notifications.all()

    context = {
        'reservation': reservation,
        'is_ready': reservation.is_ready_for_pickup(),
        'is_expired': reservation.is_expired(),
        'days_left': reservation.get_days_until_expiration(),
        'notifications': notifications,
    }
    return render(request, 'reservations/detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_reservation(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.user.is_staff:
        messages.warning(request, "Les comptes administrateur ne peuvent pas reserver un livre.")
        return redirect('catalog:book_detail', slug=book.slug)

    existing = Reservation.objects.filter(
        user=request.user, book=book, status='active'
    ).first()
    if existing:
        messages.warning(request, f'Vous avez déjà une réservation active pour "{book.title}".')
        return redirect('reservations:detail', pk=existing.pk)

    if request.method == 'POST':
        try:
            expiration_date = timezone.now() + timedelta(days=30)
            reservation = Reservation.objects.create(
                user=request.user,
                book=book,
                expiration_date=expiration_date,
            )
            ReservationQueue.objects.get_or_create(book=book)
            refresh_queue_and_notify_next(book)

            # Rafraîchir pour avoir la position mise à jour
            reservation.refresh_from_db()
            create_reservation_notification(
                reservation,
                'ready_for_pickup' if reservation.is_ready_for_pickup() else 'created',
                f'Reservation creee pour "{book.title}". Position actuelle: {reservation.queue_position}.',
            )
            messages.success(request, f'Réservation créée. Position : {reservation.queue_position}')
            return redirect('reservations:detail', pk=reservation.pk)

        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
            # ✅ Correction: slug au lieu de pk
            return redirect('catalog:book_detail', slug=book.slug)

    return render(request, 'reservations/create.html', {'book': book})


@login_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)

    if reservation.status != 'active':
        messages.warning(request, 'Cette réservation ne peut pas être annulée.')
        return redirect('reservations:list')

    if request.method == 'POST':
        reservation.status = 'cancelled'
        reservation.save()

        create_reservation_notification(
            reservation,
            'cancelled',
            f'Reservation annulee pour "{reservation.book.title}".',
        )
        refresh_queue_and_notify_next(reservation.book)

        messages.success(request, f'Réservation pour "{reservation.book.title}" annulée.')
        return redirect('reservations:list')

    # ✅ Correction: parenthèse fermante en trop supprimée
    return render(request, 'reservations/confirm_cancel.html', {'reservation': reservation})
