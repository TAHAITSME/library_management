from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cart

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """Crée un panier utilisateur après création d'un utilisateur"""
    if created:
        Cart.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_cart(sender, instance, **kwargs):
    """Sauvegarde le panier utilisateur après modification"""
    instance.cart.save()
