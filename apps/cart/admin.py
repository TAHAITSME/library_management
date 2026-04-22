from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at', 'updated_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email',)
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'book', 'quantity', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('cart__user__email', 'book__title')
    
    def get_user(self, obj):
        """Display the user who owns the cart"""
        return obj.cart.user
    get_user.short_description = 'User'
