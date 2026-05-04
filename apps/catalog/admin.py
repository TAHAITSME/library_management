from django.contrib import admin
from .models import Category, Author, Book, Review, Wishlist, WishlistItem


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'helpful_count', 'created_at', 'updated_at')
    can_delete = True
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'books_count', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at',)

    def books_count(self, obj):
        return obj.books.count()
    books_count.short_description = 'Nombre de livres'


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'nationality', 'birth_date', 'books_count', 'created_at')
    search_fields = ('first_name', 'last_name', 'nationality', 'biography')
    list_filter = ('nationality', 'created_at')
    ordering = ('last_name', 'first_name')
    readonly_fields = ('created_at',)

    def books_count(self, obj):
        return obj.books.count()
    books_count.short_description = 'Livres'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'category',
        'price',
        'status',
        'available_copies',
        'total_copies',
        'rating',
        'created_at',
    )
    list_filter = (
        'status',
        'category',
        'author',
        'language',
        'publication_date',
        'created_at',
    )
    search_fields = (
        'title',
        'slug',
        'isbn',
        'publisher',
        'author__first_name',
        'author__last_name',
        'category__name',
    )
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'rating', 'number_of_reviews')
    autocomplete_fields = ('author', 'category')
    list_editable = ('status', 'price', 'available_copies')
    inlines = [ReviewInline]

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'slug', 'isbn', 'author', 'category', 'description')
        }),
        ('Publication', {
            'fields': ('publisher', 'publication_date', 'pages', 'language')
        }),
        ('Tarification et image', {
            'fields': ('price', 'cover_image')
        }),
        ('Inventaire', {
            'fields': ('total_copies', 'available_copies', 'status')
        }),
        ('Évaluation', {
            'fields': ('rating', 'number_of_reviews')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'helpful_count', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    autocomplete_fields = ('book',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_item_count', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WishlistItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wishlist', 'book', 'priority', 'added_at')
    list_filter = ('priority', 'added_at')
    search_fields = ('wishlist__user__username', 'book__title')
    autocomplete_fields = ('wishlist', 'book')