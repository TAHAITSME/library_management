from django.conf import settings
from django.db import models


class StockMovement(models.Model):
    """Trace les ajustements manuels faits depuis le backoffice."""

    REASON_CHOICES = [
        ('manual', 'Ajustement manuel'),
        ('purchase', 'Approvisionnement'),
        ('correction', 'Correction'),
        ('loss', 'Perte'),
        ('return', 'Retour'),
    ]

    book = models.ForeignKey('catalog.Book', on_delete=models.CASCADE, related_name='stock_movements')
    previous_total = models.PositiveIntegerField()
    new_total = models.PositiveIntegerField()
    previous_available = models.PositiveIntegerField()
    new_available = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='manual')
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'

    def __str__(self):
        return f'{self.book} ({self.previous_available} -> {self.new_available})'
