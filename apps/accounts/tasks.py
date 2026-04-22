from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from .models import CustomUser
import logging
import os

logger = logging.getLogger(__name__)


def get_base_url():
    """Get the base URL from environment or settings"""
    return os.getenv('SITE_URL', 'http://localhost:8000')


@shared_task
def send_welcome_email(user_id):
    """Envoyer un email de bienvenue au nouvel utilisateur"""
    try:
        user = CustomUser.objects.get(id=user_id)
        subject = f'Bienvenue {user.first_name}! 🎉'
        base_url = get_base_url()
        login_url = f'{base_url}/accounts/login/'
        
        context = {
            'user': user,
            'login_url': login_url,
        }
        
        html_message = render_to_string('emails/welcome.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {user.email}")
    except CustomUser.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error sending welcome email for user {user_id}: {str(e)}", exc_info=True)


@shared_task
def send_password_reset_email(user_id, reset_token):
    """Envoyer email de réinitialisation mot de passe"""
    try:
        user = CustomUser.objects.get(id=user_id)
        subject = 'Réinitialiser votre mot de passe 🔐'
        base_url = get_base_url()
        reset_url = f'{base_url}/accounts/reset/{reset_token}/'
        
        context = {
            'user': user,
            'reset_token': reset_token,
            'reset_url': reset_url,
        }
        
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Error sending password reset email for user {user_id}: {str(e)}", exc_info=True)


@shared_task
def send_order_confirmation_email(order_id):
    """Envoyer confirmation commande"""
    try:
        from apps.orders.models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Confirmation commande #{order.order_number} 📦'
        base_url = get_base_url()
        tracking_url = f'{base_url}/orders/{order.id}/'
        
        context = {
            'order': order,
            'user': order.user,
            'tracking_url': tracking_url,
        }
        
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Order confirmation email sent to {order.user.email} for order {order.id}")
    except Exception as e:
        logger.error(f"Error sending order confirmation email for order {order_id}: {str(e)}", exc_info=True)


@shared_task
def send_borrow_reminder_email(borrow_id):
    """Rappel avant expiration emprunt (3 jours avant)"""
    try:
        from apps.borrowing.models import Borrow
        borrow = Borrow.objects.get(id=borrow_id)
        
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
        from apps.borrowing.models import Borrow
        borrow = Borrow.objects.get(id=borrow_id)
        
        if borrow.is_overdue:
            days_overdue = (timezone.now() - borrow.due_date).days
            
            subject = f'⚠️ Livre en retard: "{borrow.book.title}" (Pénalité: {borrow.fine_amount}€)'
            
            context = {
                'borrow': borrow,
                'user': borrow.user,
                'days_overdue': days_overdue,
                'fine_amount': borrow.fine_amount,
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
def send_review_receipt_email(review_id):
    """Confirmation publication avis"""
    try:
        from apps.catalog.models import Review
        review = Review.objects.get(id=review_id)
        
        subject = f'✅ Votre avis sur "{review.book.title}" a été publié!'
        
        context = {
            'review': review,
            'user': review.user,
            'book': review.book,
        }
        
        html_message = render_to_string('emails/review_receipt.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [review.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Review receipt email sent to {review.user.email} for review {review.id}")
    except Exception as e:
        logger.error(f"Error sending review receipt email for review {review_id}: {str(e)}", exc_info=True)
