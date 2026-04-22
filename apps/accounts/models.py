from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    """Utilisateur personalisé avec champs supplémentaires"""
    
    ROLE_CHOICES = [
        ('student', 'Étudiant'),
        ('teacher', 'Professeur'),
        ('admin', 'Administrateur'),
        ('staff', 'Personnel'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    avatar = models.URLField(null=True, blank=True, help_text='URL de l\'avatar')
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active_member = models.BooleanField(default=True)
    membership_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"


class Profile(models.Model):
    """Profil utilisateur avec statistiques"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    total_books_borrowed = models.IntegerField(default=0)
    total_books_purchased = models.IntegerField(default=0)
    total_amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    number_of_reservations = models.IntegerField(default=0)
    last_login_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
    
    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"
