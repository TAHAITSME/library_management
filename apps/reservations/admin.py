from django.contrib import admin
from .models import Reservation, ReservationQueue, ReservationNotification


class ReservationNotificationInline(admin.TabularInline):
    model = ReservationNotification
    extra = 0
    readonly_fields = ('notification_type', 'message', 'is_sent', 'sent_at', 'created_at')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'book',
        'status',
        'queue_position',
        'reservation_date',
        'expiration_date',
        'pickup_date',
        'ready_for_pickup',
    )
    list_filter = ('status', 'reservation_date', 'expiration_date', 'pickup_date')
    search_fields = ('user__username', 'user__email', 'book__title')
    readonly_fields = ('reservation_date',)
    autocomplete_fields = ('user', 'book')
    inlines = [ReservationNotificationInline]

    def ready_for_pickup(self, obj):
        return obj.is_ready_for_pickup()
    ready_for_pickup.boolean = True
    ready_for_pickup.short_description = 'Prêt ?'


@admin.register(ReservationQueue)
class ReservationQueueAdmin(admin.ModelAdmin):
    list_display = ('book', 'total_reservations')
    search_fields = ('book__title',)
    autocomplete_fields = ('book',)


@admin.register(ReservationNotification)
class ReservationNotificationAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'notification_type', 'is_sent', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'is_sent', 'created_at')
    search_fields = ('reservation__user__username', 'reservation__book__title', 'message')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('reservation',)