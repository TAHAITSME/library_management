from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Borrow(models.Model):
    """Emprunt de livre"""
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('returned', 'Retourné'),
        ('overdue', 'En retard'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrows')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='borrows')
    
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()  # Date limite de retour
    return_date = models.DateTimeField(null=True, blank=True)  # Date réelle de retour
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Pénalités
    is_overdue = models.BooleanField(default=False)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-borrow_date']
        verbose_name = 'Emprunt'
        verbose_name_plural = 'Emprunts'
    
    def __str__(self):
        return f"{self.user} - {self.book.title}"
    
    def is_overdue_now(self):
        """Vérifier si l'emprunt est en retard"""
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date
    
    def get_days_left(self):
        """Obtenir le nombre de jours restants"""
        if self.status == 'returned':
            return 0
        return (self.due_date - timezone.now().date()).days
    
    def calculate_fine(self):
        """Calculer la pénalité de retard"""
        if self.return_date:
            overdue_days = (self.return_date.date() - self.due_date).days
        else:
            overdue_days = (timezone.now().date() - self.due_date).days
        
        if overdue_days > 0:
            self.fine_amount = overdue_days * 1  # 1€ par jour de retard
            self.is_overdue = True
        
        return self.fine_amount


class BorrowRequest(models.Model):
    """Demande d'emprunt en attente"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='borrow_requests')
    
    requested_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Traitement
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']
        unique_together = ['user', 'book']
        verbose_name = 'Demande d\'emprunt'
        verbose_name_plural = 'Demandes d\'emprunt'
    
    def __str__(self):
        return f"Demande {self.user} - {self.book.title}"
