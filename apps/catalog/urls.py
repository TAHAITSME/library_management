from django.urls import path
from . import views
from .wishlist_views import (
    wishlist_view, add_to_wishlist, remove_from_wishlist,
    update_wishlist_priority, wishlist_api
)

app_name = 'catalog'

urlpatterns = [
    path('', views.books_list_view, name='books_list'),
    path('book/<slug:slug>/', views.book_detail_view, name='book_detail'),
    path('category/<int:category_id>/', views.category_books_view, name='category_books'),
    path('author/<int:author_id>/', views.author_books_view, name='author_books'),
    path('search/', views.search_books_view, name='search'),
    path('book/<int:book_id>/review/', views.add_review_view, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review_view, name='delete_review'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    
    # Wishlist URLs
    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/api/', wishlist_api, name='wishlist_api'),
    path('wishlist/add/<int:book_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/update/<int:item_id>/', update_wishlist_priority, name='update_wishlist_priority'),
]
