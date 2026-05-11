from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.reservations.models import Reservation
from apps.reservations.views import create_reservation_notification, refresh_queue_and_notify_next


class Command(BaseCommand):
    help = 'Expire les reservations actives depassees et notifie les utilisateurs suivants.'

    def handle(self, *args, **options):
        expired = 0
        reservations = Reservation.objects.select_related('book', 'user').filter(
            status='active',
            expiration_date__lt=timezone.now(),
        )

        for reservation in reservations:
            reservation.status = 'expired'
            reservation.save(update_fields=['status'])
            create_reservation_notification(
                reservation,
                'expired',
                f'Votre reservation pour "{reservation.book.title}" a expire.',
            )
            refresh_queue_and_notify_next(reservation.book)
            expired += 1

        self.stdout.write(self.style.SUCCESS(f'{expired} reservation(s) expiree(s).'))
