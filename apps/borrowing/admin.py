from django.contrib import admin
from .models import Borrow, BorrowRequest


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'book',
        'status',
        'borrow_date',
        'due_date',
        'return_date',
        'is_overdue',
        'fine_amount',
        'fine_paid',
        'days_left',
    )
    list_filter = ('status', 'is_overdue', 'fine_paid', 'borrow_date', 'due_date', 'return_date')
    search_fields = ('user__username', 'user__email', 'book__title')
    readonly_fields = ('borrow_date',)
    autocomplete_fields = ('user', 'book')

    def days_left(self, obj):
        return obj.get_days_left()
    days_left.short_description = 'Jours restants'


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'book',
        'status',
        'requested_date',
        'approved_by',
        'approval_date',
    )
    list_filter = ('status', 'requested_date', 'approval_date')
    search_fields = ('user__username', 'user__email', 'book__title')
    readonly_fields = ('requested_date',)
    autocomplete_fields = ('user', 'book', 'approved_by')