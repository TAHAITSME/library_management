from django.contrib import admin
from .models import Reservation, ReservationQueue, ReservationNotification


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'status', 'queue_position', 'reservation_date', 'expiration_date')
    list_filter = ('status', 'reservation_date', 'book')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('reservation_date', 'pickup_date')
    fieldsets = (
        ('Information générale', {
            'fields': ('user', 'book', 'status')
        }),
        ('Dates', {
            'fields': ('reservation_date', 'expiration_date', 'pickup_date')
        }),
        ('File d\'attente', {
            'fields': ('queue_position',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Mettre à jour la file d'attente
        if obj.book.reservation_queue:
            obj.book.reservation_queue.update_queue_positions()


@admin.register(ReservationQueue)
class ReservationQueueAdmin(admin.ModelAdmin):
    list_display = ('book', 'total_reservations')
    readonly_fields = ('total_reservations',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Édition
            return self.readonly_fields + ['book']
        return self.readonly_fields


@admin.register(ReservationNotification)
class ReservationNotificationAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'notification_type', 'is_sent', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'is_sent', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Notification', {
            'fields': ('reservation', 'notification_type', 'message')
        }),
        ('Envoi', {
            'fields': ('is_sent', 'sent_at')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )
