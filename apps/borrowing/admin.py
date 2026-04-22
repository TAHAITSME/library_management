from django.contrib import admin
from .models import Borrow, BorrowRequest


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrow_date', 'due_date', 'status', 'is_overdue', 'fine_amount')
    list_filter = ('status', 'is_overdue', 'borrow_date')
    search_fields = ('user__email', 'book__title')
    readonly_fields = ('borrow_date', 'return_date')


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'requested_date')
    list_filter = ('status', 'requested_date')
    search_fields = ('user__email', 'book__title')
