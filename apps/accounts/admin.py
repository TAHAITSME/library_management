from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin pour CustomUser"""
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active_member', 'membership_date')
    list_filter = ('role', 'is_active_member', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'avatar', 'bio', 'phone', 'address', 'date_of_birth', 'is_active_member')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'phone')}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin pour Profile"""
    
    list_display = ('user', 'total_books_borrowed', 'total_amount_spent', 'account_balance')
    list_filter = ('total_books_borrowed', 'total_amount_spent')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('total_books_borrowed', 'total_books_purchased', 'total_amount_spent', 'number_of_reservations')
