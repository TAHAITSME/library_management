#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour ajouter des données d'exemple à la base de données
"""
import os
import django
import re
import unicodedata

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from apps.catalog.models import Category, Author, Book
from django.contrib.auth.models import User

def create_slug(title):
    """Crée un slug valide à partir du titre (sans accents)"""
    # Remplacer les accents
    nfkd_form = unicodedata.normalize('NFKD', title)
    slug = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Convertir en minuscules et remplacer les espaces/caractères spéciaux
    slug = re.sub(r'[^\w\s-]', '', slug).lower()
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug

# Créer les catégories
categories_data = [
    {'name': 'Science-Fiction', 'icon': 'fas fa-rocket'},
    {'name': 'Roman', 'icon': 'fas fa-book'},
    {'name': 'Thriller', 'icon': 'fas fa-skull'},
    {'name': 'Mystère', 'icon': 'fas fa-mask'},
    {'name': 'Fantaisie', 'icon': 'fas fa-wand-magic-sparkles'},
    {'name': 'Jeunesse', 'icon': 'fas fa-child'},
]

print("📚 Ajout des catégories...")
for cat_data in categories_data:
    cat, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'icon': cat_data['icon']}
    )
    if created:
        print(f"  ✓ {cat.name}")
    else:
        print(f"  ✗ {cat.name} (existe déjà)")

# Créer les auteurs
authors_data = [
    {'first_name': 'Jules', 'last_name': 'Verne', 'nationality': 'Français'},
    {'first_name': 'Isaac', 'last_name': 'Asimov', 'nationality': 'Américain'},
    {'first_name': 'George', 'last_name': 'Orwell', 'nationality': 'Britannique'},
    {'first_name': 'Agatha', 'last_name': 'Christie', 'nationality': 'Britannique'},
    {'first_name': 'J.K.', 'last_name': 'Rowling', 'nationality': 'Britannique'},
    {'first_name': 'Victor', 'last_name': 'Hugo', 'nationality': 'Français'},
]

print("\n✍️  Ajout des auteurs...")
authors = {}
for author_data in authors_data:
    author, created = Author.objects.get_or_create(
        first_name=author_data['first_name'],
        last_name=author_data['last_name'],
        defaults={'nationality': author_data['nationality']}
    )
    authors[f"{author.first_name} {author.last_name}"] = author
    if created:
        print(f"  ✓ {author.first_name} {author.last_name}")
    else:
        print(f"  ✗ {author.first_name} {author.last_name} (existe déjà)")

# Créer les livres
books_data = [
    {
        'title': '20 000 lieues sous les mers',
        'isbn': '978-2-07-036743-2',
        'author': 'Jules Verne',
        'category': 'Science-Fiction',
        'description': 'Une aventure épique sous les océans à bord du Nautilus du Capitaine Nemo.',
        'price': 12.99,
        'publication_date': '1870-11-20',
        'publisher': 'Pierre-Jules Hetzel',
        'pages': 620,
        'language': 'Français',
        'total_copies': 5,
        'cover_image': 'https://images.unsplash.com/photo-1507842217343-583f20270319?w=400'
    },
    {
        'title': 'Le Voyage au centre de la terre',
        'isbn': '978-2-07-036744-9',
        'author': 'Jules Verne',
        'category': 'Science-Fiction',
        'description': 'Une expédition extraordinaire vers les profondeurs de la terre.',
        'price': 11.99,
        'publication_date': '1864-05-29',
        'publisher': 'Pierre-Jules Hetzel',
        'pages': 480,
        'language': 'Français',
        'total_copies': 4,
        'cover_image': 'https://images.unsplash.com/photo-1504995617288-701f88f82281?w=400'
    },
    {
        'title': 'Fondation',
        'isbn': '978-2-07-036021-1',
        'author': 'Isaac Asimov',
        'category': 'Science-Fiction',
        'description': 'Le chef-d\'œuvre de la science-fiction: une épopée galactique incontournable.',
        'price': 14.99,
        'publication_date': '1951-06-01',
        'publisher': 'Éditions Denoël',
        'pages': 450,
        'language': 'Français',
        'total_copies': 3,
        'cover_image': 'https://images.unsplash.com/photo-1519904981063-b0cf448d479e?w=400'
    },
    {
        'title': '1984',
        'isbn': '978-2-07-036020-4',
        'author': 'George Orwell',
        'category': 'Thriller',
        'description': 'Un roman dystopique parmi les plus influents du XXe siècle.',
        'price': 8.99,
        'publication_date': '1949-06-08',
        'publisher': 'Éditions Gallimard',
        'pages': 428,
        'language': 'Français',
        'total_copies': 6,
        'cover_image': 'https://images.unsplash.com/photo-1543002588-d83cdf395fda?w=400'
    },
    {
        'title': 'Assassinat sur le Nil',
        'isbn': '978-2-253-04650-7',
        'author': 'Agatha Christie',
        'category': 'Mystère',
        'description': 'Un chef-d\'œuvre du roman policier sur le Nil.',
        'price': 7.99,
        'publication_date': '1937-09-01',
        'publisher': 'Le Livre de Poche',
        'pages': 315,
        'language': 'Français',
        'total_copies': 4,
        'cover_image': 'https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=400'
    },
    {
        'title': 'Harry Potter à l\'école des sorciers',
        'isbn': '978-2-07-061275-8',
        'author': 'J.K. Rowling',
        'category': 'Jeunesse',
        'description': 'Le premier tome de la saga Harry Potter, un classique de la littérature jeunesse.',
        'price': 9.99,
        'publication_date': '1997-06-26',
        'publisher': 'Éditions Gallimard Jeunesse',
        'pages': 336,
        'language': 'Français',
        'total_copies': 5,
        'cover_image': 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400'
    },
    {
        'title': 'Les Misérables',
        'isbn': '978-2-07-036745-6',
        'author': 'Victor Hugo',
        'category': 'Roman',
        'description': 'L\'épopée du peuple français racontée à travers la vie de Jean Valjean.',
        'price': 15.99,
        'publication_date': '1862-04-16',
        'publisher': 'Éditions Gallimard',
        'pages': 1232,
        'language': 'Français',
        'total_copies': 3,
        'cover_image': 'https://images.unsplash.com/photo-1543002588-d83cdf395fda?w=400'
    },
]

print("\n📖 Ajout des livres...")
for book_data in books_data:
    # Récupérer l'auteur et la catégorie
    author = authors.get(book_data['author'])
    category = Category.objects.get(name=book_data['category'])
    
    if not author:
        print(f"  ✗ {book_data['title']} (auteur non trouvé)")
        continue
    
    # Créer le slug VALIDE (sans accents)
    slug = create_slug(book_data['title'])
    
    book, created = Book.objects.get_or_create(
        isbn=book_data['isbn'],
        defaults={
            'title': book_data['title'],
            'slug': slug,
            'author': author,
            'category': category,
            'description': book_data['description'],
            'price': book_data['price'],
            'publication_date': book_data['publication_date'],
            'publisher': book_data['publisher'],
            'pages': book_data['pages'],
            'language': book_data['language'],
            'total_copies': book_data['total_copies'],
            'available_copies': book_data['total_copies'],
            'cover_image': book_data['cover_image'],
            'status': 'available'
        }
    )
    
    if created:
        print(f"  ✓ {book.title}")
    else:
        print(f"  ✗ {book.title} (existe déjà)")

print("\n✅ Données d'exemple ajoutées avec succès!")
print("\n💻 Accédez à l'admin: http://127.0.0.1:8000/admin/")
