from django.contrib import admin
from .models import Category, Author, Book, Review, Wishlist, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'nationality', 'created_at')
    list_filter = ('nationality', 'created_at')
    search_fields = ('first_name', 'last_name')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'price', 'available_copies', 'status', 'created_at')
    list_filter = ('status', 'category', 'language', 'created_at')
    search_fields = ('title', 'isbn', 'author__first_name', 'author__last_name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('rating', 'number_of_reviews', 'created_at', 'updated_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'book__title')
    readonly_fields = ('created_at', 'updated_at')


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ('added_at',)
    fields = ('book', 'priority', 'added_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_item_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WishlistItemInline]

    def get_item_count(self, obj):
        return obj.get_item_count()
    get_item_count.short_description = 'Nombre d\'articles'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('book', 'get_user', 'priority', 'added_at')
    list_filter = ('priority', 'added_at')
    search_fields = ('book__title', 'wishlist__user__email')
    readonly_fields = ('added_at',)

    def get_user(self, obj):
        return obj.wishlist.user
    get_user.short_description = 'Utilisateur'
