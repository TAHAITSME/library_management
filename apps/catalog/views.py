from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Book, Category, Author, Review
from .forms import ReviewForm
from apps.borrowing.models import Borrow


def get_recommendations_for_user(user, limit=8):
    """Générer des recommandations réelles basées sur l'historique de l'utilisateur"""
    recommendations = Book.objects.none()
    
    if not user.is_authenticated:
        # Pour les utilisateurs non authentifiés: livres populaires
        return Book.objects.filter(status='available').annotate(
            borrow_count=Count('borrows')
        ).order_by('-borrow_count', '-rating')[:limit]
    
    # Récupérer les catégories et auteurs des livres empruntés par l'utilisateur
    borrowed_books = Borrow.objects.filter(user=user).values_list('book_id', flat=True)
    
    if borrowed_books.exists():
        borrowed_book_objs = Book.objects.filter(id__in=borrowed_books)
        categories = borrowed_book_objs.values_list('category_id', flat=True).distinct()
        authors = borrowed_book_objs.values_list('author_id', flat=True).distinct()
        
        # Recommandations: livres de même catégorie/auteur, non empruntés
        recommendations = Book.objects.filter(
            status='available'
        ).exclude(
            id__in=borrowed_books
        ).filter(
            Q(category_id__in=categories) | Q(author_id__in=authors)
        ).annotate(
            borrow_count=Count('borrows')
        ).order_by('-rating', '-borrow_count', '-created_at')[:limit]
    
    # Si pas assez de recommandations: ajouter les livres populaires
    if recommendations.count() < limit:
        popular_books = Book.objects.filter(
            status='available'
        ).exclude(
            id__in=recommendations.values_list('id', flat=True)
        ).exclude(
            id__in=borrowed_books
        ).annotate(
            borrow_count=Count('borrows')
        ).order_by('-rating', '-borrow_count')[:limit - recommendations.count()]
        recommendations = recommendations | popular_books
    
    return recommendations[:limit]


def books_list_view(request):
    books = Book.objects.filter(status='available').select_related('author', 'category')
    categories = Category.objects.all()
    authors = Author.objects.all()
    
    # Filtre recherche
    query = request.GET.get('q', request.GET.get('search', ''))
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(isbn__icontains=query)
        ).distinct()

    # Filtre prix
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            books = books.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            books = books.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Filtre catégorie
    category_id = request.GET.get('category')
    if category_id and category_id.isdigit():
        books = books.filter(category_id=category_id)

    # Filtre auteur (NEW)
    author_id = request.GET.get('author')
    if author_id and author_id.isdigit():
        books = books.filter(author_id=author_id)

    # Filtre rating
    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            books = books.filter(rating__gte=float(min_rating))
        except ValueError:
            pass

    # Filtre année de publication (NEW)
    year = request.GET.get('year')
    if year:
        try:
            year_int = int(year)
            books = books.filter(publication_date__year=year_int)
        except (ValueError, TypeError):
            pass

    # Filtre langue (NEW)
    language = request.GET.get('language')
    if language:
        books = books.filter(language=language)

    # Tri
    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'title': 'title',
        'title_desc': '-title',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-rating',
        'popular': '-rating',
    }
    order = sort_map.get(sort, '-created_at')
    books = books.order_by(order)

    # Pagination
    paginator = Paginator(books, 12)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Récupérer les années et langues disponibles (optimized)
    # Cache these values or reduce queries by filtering from already-fetched books
    available_books = books.filter(status='available')  # Reuse filtered queryset
    available_years = sorted(set(
        available_books.values_list('publication_date__year', flat=True)
    ), reverse=True)
    available_languages = sorted(set(
        available_books.values_list('language', flat=True)
    ))

    current_params = request.GET.copy()
    if 'page' in current_params:
        current_params.pop('page')

    context = {
        'page_obj': page_obj,
        'books': page_obj.object_list,
        'categories': categories,
        'authors': authors,
        'available_years': available_years,
        'available_languages': available_languages,
        'current_category': category_id,
        'current_author': author_id,
        'current_year': year,
        'current_language': language,
        'current_sort': sort,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'min_rating': min_rating,
        'books_count': paginator.count,
        'is_paginated': page_obj.has_other_pages(),
        'current_params': current_params.urlencode(),
    }
    return render(request, 'catalog/books_list.html', context)


def book_detail_view(request, slug):
    book = get_object_or_404(Book, slug=slug)
    reviews = book.reviews.select_related('user').order_by('-created_at')
    
    # Recommandations intelligentes
    recommended_books = Book.objects.filter(
        status='available'
    ).exclude(
        id=book.id
    ).filter(
        Q(category=book.category) | Q(author=book.author)
    ).select_related('author').annotate(
        borrow_count=Count('borrows')
    ).order_by('-rating', '-borrow_count')[:4]

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    context = {
        'book': book,
        'reviews': reviews,
        'related_books': recommended_books,
        'avg_rating': round(avg_rating, 1),
        'user_review': user_review,
    }
    return render(request, 'catalog/book_detail.html', context)


def category_books_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    books = category.books.filter(status='available').select_related('author')
    categories = Category.objects.all()
    context = {
        'category': category,
        'books': books,
        'categories': categories,
    }
    return render(request, 'catalog/category_books.html', context)


def author_books_view(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    books = author.books.filter(status='available')
    context = {
        'author': author,
        'books': books,
    }
    return render(request, 'catalog/author_books.html', context)


def search_books_view(request):
    query = request.GET.get('q', '')
    books = Book.objects.none()

    if query:
        books = Book.objects.filter(status='available').filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(isbn__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query)
        ).distinct().select_related('author', 'category')

        sort_map = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'title': 'title',
            'price_low': 'price',
            'price_high': '-price',
            'rating': '-rating',
            '-created_at': '-created_at',
        }
        sort = sort_map.get(request.GET.get('sort', 'newest'), '-created_at')
        books = books.order_by(sort)

    context = {
        'books': books,
        'query': query,
        'books_count': books.count(),
    }
    return render(request, 'catalog/search_results.html', context)


@login_required
def add_review_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    review = Review.objects.filter(user=request.user, book=book).first()

    if request.method == 'POST':
        post_data = request.POST.copy()
        if 'content' in post_data and 'comment' not in post_data:
            post_data['comment'] = post_data.get('content', '')

        form = ReviewForm(post_data, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book = book
            # Ensure rating is set before saving
            if not review.rating:
                messages.error(request, 'Veuillez sélectionner une note.')
                return render(request, 'catalog/add_review.html', {'form': form, 'book': book})
            review.save()
            
            # Update book rating
            avg_rating = book.reviews.aggregate(Avg('rating'))['rating__avg']
            book.rating = round(avg_rating or 0, 2)
            book.number_of_reviews = book.reviews.count()
            book.save(update_fields=['rating', 'number_of_reviews'])
            messages.success(request, 'Avis publié avec succès!')
            return redirect('catalog:book_detail', slug=book.slug)
        else:
            messages.error(request, 'Erreur : veuillez vérifier votre avis.')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'catalog/add_review.html', {'form': form, 'book': book})


@login_required
def delete_review_view(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    book = review.book
    review.delete()
    avg_rating = book.reviews.aggregate(Avg('rating'))['rating__avg']
    book.rating = round(avg_rating or 0, 2)
    book.number_of_reviews = book.reviews.count()
    book.save(update_fields=['rating', 'number_of_reviews'])
    messages.success(request, 'Avis supprimé.')
    return redirect('catalog:book_detail', slug=book.slug)


def get_user_recommendations(user, limit=6):
    borrowed_ids = Borrow.objects.filter(user=user).values_list('book_id', flat=True)
    borrowed_categories = Borrow.objects.filter(
        user=user
    ).values_list('book__category_id', flat=True).distinct()

    recommendations = list(
        Book.objects.filter(
            category_id__in=borrowed_categories,
            status='available'
        ).exclude(id__in=borrowed_ids)
        .select_related('author', 'category')
        .order_by('-rating')[:limit]
    )

    if len(recommendations) < limit:
        popular = list(
            Book.objects.filter(
                status='available',
                number_of_reviews__gt=0
            ).exclude(id__in=borrowed_ids)
            .exclude(id__in=[b.id for b in recommendations])
            .select_related('author', 'category')
            .order_by('-rating', '-number_of_reviews')[:limit - len(recommendations)]
        )
        recommendations.extend(popular)

    return recommendations[:limit]


@login_required
def recommendations_view(request):
    recommendations = get_user_recommendations(request.user, limit=9)
    top_books = Book.objects.filter(
        status='available', number_of_reviews__gt=0
    ).select_related('author').order_by('-rating')[:6]

    context = {
        'recommendations': recommendations,
        'top_books': top_books,
        'has_recommendations': len(recommendations) > 0,
    }
    return render(request, 'catalog/recommendations.html', context)


def get_recommendations_context(user):
    # ✅ Correction: parenthèse fermante en trop supprimée
    if user.is_authenticated:
        return {'sidebar_recommendations': get_user_recommendations(user, limit=4)}
    return {'sidebar_recommendations': []}
