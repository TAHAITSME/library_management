from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Cart(models.Model):
    """Panier de l'utilisateur"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Panier'
        verbose_name_plural = 'Paniers'
    
    def __str__(self):
        return f"Panier de {self.user}"
    
    def get_total(self):
        """Calculer le total du panier"""
        return sum(item.get_total() for item in self.items.all())
    
    def get_item_count(self):
        """Nombre d'articles dans le panier"""
        return self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0
    
    def clear(self):
        """Vider le panier"""
        self.items.all().delete()


class CartItem(models.Model):
    """Article du panier"""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('catalog.Book', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'book']  # ✓ Fixed: Should be cart+book, not user+book
        verbose_name = 'Article du panier'
        verbose_name_plural = 'Articles du panier'
    
    def __str__(self):
        return f"{self.cart.user} - {self.book} (x{self.quantity})"
    
    def get_total(self):
        """Calculer le total pour cet article"""
        return self.book.price * self.quantity
    
    def can_add_to_cart(self):
        """Vérifier si on peut ajouter cet article au panier"""
        return self.book.available_copies > 0
