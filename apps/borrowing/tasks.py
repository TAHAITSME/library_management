from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import os

logger = logging.getLogger(__name__)


def get_base_url():
    """Get the base URL from environment or settings"""
    return os.getenv('SITE_URL', 'http://localhost:8000')


@shared_task
def send_borrow_confirmation_email(borrow_id):
    """Envoyer confirmation d'emprunt approuvé"""
    try:
        from .models import Borrow
        borrow = Borrow.objects.get(id=borrow_id)
        
        subject = f'✅ Votre emprunt de "{borrow.book.title}" a été approuvé!'
        base_url = get_base_url()
        pickup_url = f'{base_url}/borrowing/'
        
        context = {
            'borrow': borrow,
            'user': borrow.user,
            'pickup_url': pickup_url,
        }
        
        html_message = render_to_string('emails/borrow_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [borrow.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Borrow confirmation email sent to {borrow.user.email} for borrow {borrow.id}")
    except Exception as e:
        logger.error(f"Error sending borrow confirmation email for borrow {borrow_id}: {str(e)}", exc_info=True)


@shared_task
def send_borrow_reminder_email(borrow_id):
    """Rappel avant expiration emprunt (3 jours avant)"""
    try:
        from .models import Borrow
        borrow = Borrow.objects.get(id=borrow_id, status='active')
        
        days_left = (borrow.due_date - timezone.now()).days
        
        if days_left <= 3 and days_left > 0:
            subject = f'⏰ Rappel: Retour du livre "{borrow.book.title}" dans {days_left} jour{"s" if days_left > 1 else ""}'
            base_url = get_base_url()
            borrowing_url = f'{base_url}/borrowing/'
            
            context = {
                'borrow': borrow,
                'user': borrow.user,
                'days_left': days_left,
                'borrowing_url': borrowing_url,
            }
            
            html_message = render_to_string('emails/borrow_reminder.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [borrow.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Borrow reminder email sent to {borrow.user.email} for borrow {borrow.id}")
    except Exception as e:
        logger.error(f"Error sending borrow reminder email for borrow {borrow_id}: {str(e)}", exc_info=True)


@shared_task
def send_overdue_book_email(borrow_id):
    """Alerte retard emprunt + pénalité"""
    try:
        from .models import Borrow
        borrow = Borrow.objects.get(id=borrow_id, status='active')
        
        if borrow.is_overdue:
            days_overdue = (timezone.now() - borrow.due_date).days
            
            subject = f'⚠️ Livre en retard: "{borrow.book.title}" (Pénalité: {borrow.fine_amount}€)'
            base_url = get_base_url()
            return_url = f'{base_url}/borrowing/'
            
            context = {
                'borrow': borrow,
                'user': borrow.user,
                'days_overdue': days_overdue,
                'fine_amount': borrow.fine_amount,
                'return_url': return_url,
            }
            
            html_message = render_to_string('emails/overdue_book.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [borrow.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Overdue book email sent to {borrow.user.email} for borrow {borrow.id}")
    except Exception as e:
        logger.error(f"Error sending overdue book email for borrow {borrow_id}: {str(e)}", exc_info=True)


@shared_task
def send_borrow_return_confirmation_email(borrow_id):
    """Confirmation retour d'emprunt"""
    try:
        from .models import Borrow
        borrow = Borrow.objects.get(id=borrow_id, status='returned')
        
        fine_info = f"Pénalité appliquée: {borrow.fine_amount}€" if borrow.fine_amount > 0 else "Aucune pénalité"
        subject = f'✅ Retour confirmé: "{borrow.book.title}"'
        
        context = {
            'borrow': borrow,
            'user': borrow.user,
            'fine_info': fine_info,
        }
        
        html_message = render_to_string('emails/borrow_return_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [borrow.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Borrow return confirmation email sent to {borrow.user.email} for borrow {borrow.id}")
    except Exception as e:
        logger.error(f"Error sending borrow return confirmation email for borrow {borrow_id}: {str(e)}", exc_info=True)
