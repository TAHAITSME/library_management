from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Reservation(models.Model):
    """Réservation de livre"""
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('cancelled', 'Annulé'),
        ('completed', 'Complété'),
        ('expired', 'Expiré'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, related_name='reservations')
    
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()  # Date d'expiration de la réservation
    pickup_date = models.DateTimeField(null=True, blank=True)  # Quand le livre a été pris
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Position dans la files d'attente
    queue_position = models.IntegerField(default=1)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['queue_position', '-reservation_date']
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
    
    def __str__(self):
        return f"Réservation {self.user} - {self.book.title}"
    
    def is_expired(self):
        """Vérifier si la réservation a expiré"""
        return timezone.now() > self.expiration_date and self.status == 'active'
    
    def is_ready_for_pickup(self):
        """Vérifier si le livre est prêt à être pris"""
        return self.status == 'active' and self.queue_position == 1 and self.book.available_copies > 0
    
    def get_days_until_expiration(self):
        """Obtenir le nombre de jours avant expiration"""
        return (self.expiration_date - timezone.now()).days


class ReservationQueue(models.Model):
    """Gestion de la file d'attente des réservations par livre"""
    
    book = models.OneToOneField('catalog.Book', on_delete=models.CASCADE, related_name='reservation_queue')
    total_reservations = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'File d\'attente de réservation'
        verbose_name_plural = 'Files d\'attente de réservation'
    
    def __str__(self):
        return f"File d'attente - {self.book.title}"
    
    def update_queue_positions(self):
        """Mettre à jour les positions de la file d'attente"""
        reservations = self.book.reservations.filter(
            status='active'
        ).order_by('reservation_date')
        
        for position, reservation in enumerate(reservations, start=1):
            reservation.queue_position = position
            reservation.save()
    
    def get_next_reservation(self):
        """Obtenir la prochaine réservation active"""
        return self.book.reservations.filter(
            status='active',
            queue_position=1
        ).first()


class ReservationNotification(models.Model):
    """Notifications pour les réservations"""
    
    TYPE_CHOICES = [
        ('created', 'Creee'),
        ('ready_for_pickup', 'Prêt pour récupération'),
        ('expiring_soon', 'Expiration bientôt'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
    ]
    
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification de réservation'
        verbose_name_plural = 'Notifications de réservation'
    
    def __str__(self):
        return f"Notification - {self.reservation.user} - {self.notification_type}"
