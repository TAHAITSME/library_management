from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class Order(models.Model):
    """Commande de livres"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, db_index=True)  # ✓ Added db_index
    
    # Livres commandés
    books = models.ManyToManyField('catalog.Book', through='OrderItem')
    
    # Prix et frais
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Adresse de livraison
    shipping_address = models.TextField()
    
    # Statuts
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
    
    def __str__(self):
        return f"Commande {self.order_number}"
    
    def generate_order_number(self):
        """Générer un numéro de commande unique"""
        import uuid
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"


class OrderItem(models.Model):
    """Article d'une commande"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Prix au moment de la commande
    
    class Meta:
        unique_together = ['order', 'book']
        verbose_name = 'Article de commande'
        verbose_name_plural = 'Articles de commande'
    
    def __str__(self):
        return f"{self.book.title} x {self.quantity}"
    
    def get_total(self):
        """Calculer le total pour cet article"""
        return self.price * self.quantity


class Payment(models.Model):
    """Paiement d'une commande"""
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Carte bancaire'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Virement bancaire'),
        ('cash', 'Espèces'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
    
    def __str__(self):
        return f"Paiement pour {self.order.order_number}"


class Invoice(models.Model):
    """Facture d'une commande"""
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Détails de facturation
    billing_address = models.TextField()
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
    
    def __str__(self):
        return f"Facture {self.invoice_number}"
    
    def generate_invoice_number(self):
        """Générer un numéro de facture unique"""
        import uuid
        return f"INV-{uuid.uuid4().hex[:8].upper()}"


class Coupon(models.Model):
    """Codes promo et codes de réduction"""
    
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    
    # Type de réduction
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage %'),
        ('fixed', 'Montant fixe €'),
    ]
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)  # % ou €
    
    # Limites
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Nombre total d'utilisations autorisées")
    times_used = models.IntegerField(default=0, editable=False)
    per_user_limit = models.IntegerField(default=1, help_text="Utilisations par utilisateur")
    
    # Montants minimums
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Montant min de commande
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Discount max
    
    # Validité
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()
    
    # Utilisateurs concernés
    applicable_to_all = models.BooleanField(default=True)
    applicable_users = models.ManyToManyField(User, blank=True, related_name='available_coupons')
    
    # Livres concernés
    applicable_books = models.ManyToManyField('catalog.Book', blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Code promo'
        verbose_name_plural = 'Codes promo'
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '€'}"
    
    def is_valid(self):
        """Vérifier si le coupon est toujours valide"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False, "Ce code promo n'est pas actif"
        
        if now < self.start_date:
            return False, "Ce code promo n'est pas encore valide"
        
        if now > self.expiry_date:
            return False, "Ce code promo a expiré"
        
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "Limite d'utilisation atteinte pour ce code promo"
        
        return True, "Code valide"
    
    def apply_discount(self, order_amount):
        """Calculer la réduction à appliquer"""
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
        else:
            discount = self.discount_value
        
        # Appliquer le plafond de réduction si spécifié
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        return discount
    
    def can_use_coupon(self, user, user_usage_count):
        """Vérifier si l'utilisateur peut utiliser ce coupon"""
        is_valid, message = self.is_valid()
        
        if not is_valid:
            return False, message
        
        # Vérifier si applicable à tous les utilisateurs
        if not self.applicable_to_all and user not in self.applicable_users.all():
            return False, "Ce code promo ne s'applique pas à votre compte"
        
        # Vérifier le limite d'utilisation par utilisateur
        if user_usage_count >= self.per_user_limit:
            return False, f"Vous avez déjà utilisé ce code promo {self.per_user_limit} fois"
        
        return True, "Code peut être utilisé"
    
    def mark_as_used(self):
        """Marquer le coupon comme utilisé une fois de plus"""
        self.times_used += 1
        self.save(update_fields=['times_used'])
