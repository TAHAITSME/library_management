from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
import logging
import os

logger = logging.getLogger(__name__)


def get_base_url():
    """Get the base URL from environment or settings"""
    return os.getenv('SITE_URL', 'http://localhost:8000')


@shared_task
def send_order_confirmation_email(order_id):
    """Envoyer confirmation commande"""
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Confirmation commande #{order.order_number} 📦'
        base_url = get_base_url()
        tracking_url = f'{base_url}/orders/{order.id}/'
        
        context = {
            'order': order,
            'user': order.user,
            'order_items': order.items.all(),
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
        return f"Email envoyé à {order.user.email}"
    except Exception as e:
        logger.error(f"Error sending order confirmation email for order {order_id}: {str(e)}", exc_info=True)
        return f"Erreur: {str(e)}"


@shared_task
def send_order_shipped_email(order_id):
    """Envoyer notification d'expédition"""
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Votre commande #{order.order_number} a été expédiée 🚚'
        base_url = get_base_url()
        tracking_url = f'{base_url}/orders/{order.id}/'
        
        context = {
            'order': order,
            'user': order.user,
            'tracking_url': tracking_url,
        }
        
        html_message = render_to_string('emails/order_shipped.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Order shipped email sent to {order.user.email} for order {order.id}")
    except Exception as e:
        logger.error(f"Error sending order shipped email for order {order_id}: {str(e)}", exc_info=True)


@shared_task
def send_order_delivered_email(order_id):
    """Envoyer notification de livraison"""
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Votre commande #{order.order_number} a été livrée ✅'
        base_url = get_base_url()
        review_url = f'{base_url}/catalog/'
        
        context = {
            'order': order,
            'user': order.user,
            'review_url': review_url,
        }
        
        html_message = render_to_string('emails/order_delivered.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Order delivered email sent to {order.user.email} for order {order.id}")
    except Exception as e:
        logger.error(f"Error sending order delivered email for order {order_id}: {str(e)}", exc_info=True)
