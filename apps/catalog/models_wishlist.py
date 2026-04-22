from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Wishlist(models.Model):
    """Liste de souhaits utilisateur"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Liste de souhaits'
        verbose_name_plural = 'Listes de souhaits'

    def __str__(self):
        return f"Wishlist de {self.user}"

    def get_item_count(self):
        """Nombre de livres dans la wishlist"""
        return self.items.count()


class WishlistItem(models.Model):
    """Article dans la liste de souhaits"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('catalog.Book', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(
        default=0,
        choices=[(0, 'Basse'), (1, 'Normale'), (2, 'Haute')],
        help_text='Niveau de priorité'
    )

    class Meta:
        unique_together = ['wishlist', 'book']
        verbose_name = 'Article wishlist'
        verbose_name_plural = 'Articles wishlist'
        ordering = ['-priority', '-added_at']

    def __str__(self):
        return f"{self.wishlist.user} - {self.book.title}"
