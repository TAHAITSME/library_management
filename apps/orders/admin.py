from django.contrib import admin
from .models import Order, OrderItem, Payment, Invoice, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__email')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'book', 'quantity', 'price')
    search_fields = ('order__order_number', 'book__title')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('order__order_number', 'transaction_id')
    readonly_fields = ('created_at',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'created_at')
    search_fields = ('invoice_number', 'order__order_number')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_value', 'discount_type', 'is_active', 'times_used', 'expiry_date')
    list_filter = ('is_active', 'discount_type', 'expiry_date', 'created_at')
    search_fields = ('code', 'description')
    readonly_fields = ('times_used', 'created_at', 'updated_at')
    fieldsets = (
        ('Code Promo', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Réduction', {
            'fields': ('discount_type', 'discount_value', 'max_discount_amount')
        }),
        ('Limites', {
            'fields': ('usage_limit', 'times_used', 'per_user_limit', 'minimum_order_amount')
        }),
        ('Validité', {
            'fields': ('start_date', 'expiry_date')
        }),
        ('Utilisateurs', {
            'fields': ('applicable_to_all', 'applicable_users')
        }),
        ('Livres', {
            'fields': ('applicable_books',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('applicable_users', 'applicable_books')
