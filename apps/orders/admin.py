from django.contrib import admin
from .models import Order, OrderItem, Payment, Invoice, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ('book',)
    readonly_fields = ('get_total',)

    def get_total(self, obj):
        if obj.pk:
            return obj.get_total()
        return "-"
    get_total.short_description = 'Total'


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'user',
        'status',
        'payment_status',
        'total',
        'items_count',
        'created_at',
        'shipped_at',
    )
    list_filter = (
        'status',
        'payment_status',
        'created_at',
        'shipped_at',
        'delivered_at',
    )
    search_fields = (
        'order_number',
        'user__username',
        'user__email',
        'shipping_address',
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user',)
    inlines = [OrderItemInline, PaymentInline, InvoiceInline]

    fieldsets = (
        ('Commande', {
            'fields': ('user', 'order_number', 'status', 'payment_status')
        }),
        ('Montants', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total')
        }),
        ('Livraison', {
            'fields': ('shipping_address',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at')
        }),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Articles'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'book', 'quantity', 'price', 'get_total')
    search_fields = ('order__order_number', 'book__title')
    list_filter = ('order__created_at',)
    autocomplete_fields = ('order', 'book')

    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'amount',
        'payment_method',
        'status',
        'transaction_id',
        'created_at',
        'completed_at',
    )
    list_filter = ('payment_method', 'status', 'created_at', 'completed_at')
    search_fields = ('order__order_number', 'transaction_id', 'order__user__username')
    autocomplete_fields = ('order',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'created_at', 'updated_at')
    search_fields = ('invoice_number', 'order__order_number', 'order__user__username')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('order',)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'discount_type',
        'discount_value',
        'is_active',
        'usage_limit',
        'times_used',
        'start_date',
        'expiry_date',
    )
    list_filter = ('discount_type', 'is_active', 'start_date', 'expiry_date', 'created_at')
    search_fields = ('code', 'description')
    filter_horizontal = ('applicable_users', 'applicable_books')
    readonly_fields = ('times_used', 'created_at', 'updated_at')