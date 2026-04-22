from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.books_list_view, name='books_list'),
    path('book/<slug:slug>/', views.book_detail_view, name='book_detail'),
    path('category/<int:category_id>/', views.category_books_view, name='category_books'),
    path('author/<int:author_id>/', views.author_books_view, name='author_books'),
    path('search/', views.search_books_view, name='search'),
    path('book/<int:book_id>/review/', views.add_review_view, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review_view, name='delete_review'),
]
