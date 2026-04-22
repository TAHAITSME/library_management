"""
Management command to create sample data for testing
Usage: python manage.py create_sample_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.catalog.models import Book, Category, Author, Review
from apps.borrowing.models import Borrow, BorrowRequest
from apps.orders.models import Order, OrderItem
from apps.cart.models import Cart, CartItem
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for development and testing'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Creating sample data...')

        # Create categories
        self.stdout.write('📚 Creating categories...')
        categories = []
        category_names = ['Fiction', 'Science', 'History', 'Technology', 'Romance', 'Mystery']
        for name in category_names:
            cat, created = Category.objects.get_or_create(name=name)
            categories.append(cat)
            if created:
                self.stdout.write(f'  ✓ Created category: {name}')

        # Create authors
        self.stdout.write('✍️ Creating authors...')
        authors = []
        author_data = [
            ('Albert', 'Einstein'),
            ('Marie', 'Curie'),
            ('Stephen', 'Hawking'),
            ('Carl', 'Sagan'),
            ('Jane', 'Austen'),
            ('George', 'Orwell'),
            ('J.K.', 'Rowling'),
            ('Isaac', 'Asimov'),
        ]
        for first, last in author_data:
            author, created = Author.objects.get_or_create(
                first_name=first,
                last_name=last
            )
            authors.append(author)
            if created:
                self.stdout.write(f'  ✓ Created author: {first} {last}')

        # Create books
        self.stdout.write('📖 Creating books...')
        books = []
        book_data = [
            ('A Brief History of Time', 'Explore the mysteries of the universe', 45.99, 10, authors[2], categories[1], 256),
            ('The Selfish Gene', 'Understanding evolution and genetics', 35.50, 8, authors[3], categories[1], 224),
            ('Pride and Prejudice', 'A classic romance novel', 15.99, 15, authors[4], categories[4], 432),
            ('1984', 'A dystopian novel about surveillance', 28.99, 12, authors[5], categories[0], 328),
            ('Foundation', 'The beginning of a galactic empire', 22.50, 10, authors[7], categories[0], 255),
            ('The Elegant Universe', 'String theory explained', 52.99, 5, authors[1], categories[1], 464),
            ('Cosmos', 'A journey through space and time', 39.99, 7, authors[3], categories[1], 496),
            ('Murder on the Orient Express', 'A classic mystery', 18.99, 10, authors[6], categories[5], 272),
        ]

        for title, desc, price, copies, author, category, pages in book_data:
            book, created = Book.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'price': price,
                    'available_copies': copies,
                    'author': author,
                    'category': category,
                    'isbn': f'ISBN-{Book.objects.count() + 1000}',
                    'publication_date': timezone.now() - timedelta(days=365),
                    'language': 'en',
                    'status': 'available',
                    'pages': pages,
                    'publisher': 'Test Publisher',
                    'slug': title.lower().replace(' ', '-'),
                }
            )
            books.append(book)
            if created:
                self.stdout.write(f'  ✓ Created book: {title}')

        # Create test users
        self.stdout.write('👥 Creating test users...')
        test_users = []
        user_data = [
            ('john@example.com', 'John', 'Doe', 'password123'),
            ('jane@example.com', 'Jane', 'Smith', 'password123'),
            ('bob@example.com', 'Bob', 'Johnson', 'password123'),
        ]

        for email, first, last, password in user_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'username': email.split('@')[0],
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'  ✓ Created user: {email} (pwd: {password})')
            test_users.append(user)

        # Create cart items
        self.stdout.write('🛒 Creating cart items...')
        for user in test_users:
            cart, _ = Cart.objects.get_or_create(user=user)
            # Add 2-3 random books to each cart
            for book in books[:2]:
                CartItem.objects.get_or_create(
                    cart=cart,
                    book=book,
                    defaults={'quantity': 1}
                )
            self.stdout.write(f'  ✓ Added items to {user.email}\'s cart')

        # Create reviews
        self.stdout.write('⭐ Creating reviews...')
        for user in test_users:
            for book in books[:4]:
                Review.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={
                        'rating': (hash(f'{user.id}{book.id}') % 5) + 1,
                        'comment': f'Great book! I really enjoyed reading {book.title}.',
                    }
                )
        self.stdout.write(f'  ✓ Created {Review.objects.count()} reviews')

        # Create borrows
        self.stdout.write('📋 Creating borrow records...')
        for i, user in enumerate(test_users[:2]):
            for j, book in enumerate(books[:3]):
                borrow, created = Borrow.objects.get_or_create(
                    user=user,
                    book=book,
                    defaults={
                        'borrow_date': timezone.now() - timedelta(days=10 + i*5),
                        'due_date': timezone.now() + timedelta(days=20 - i*5),
                        'status': 'active',
                        'is_overdue': False,
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created borrow: {user.email} borrowed {book.title}')

        # Create orders
        self.stdout.write('📦 Creating orders...')
        for i, user in enumerate(test_users):
            order = Order.objects.create(
                user=user,
                order_number=f'ORD-TEST-{i+1:03d}',
                subtotal=99.99,
                shipping_cost=5.00,
                tax=10.00,
                total=114.99,
                shipping_address=f'{i*100} Test Street, Test City',
                status='processing' if i % 2 == 0 else 'shipped',
                payment_status='paid',
            )
            
            # Add order items
            for j, book in enumerate(books[i:i+2]):
                OrderItem.objects.create(
                    order=order,
                    book=book,
                    quantity=1,
                    price=book.price,
                )
            self.stdout.write(f'  ✓ Created order {order.order_number}')

        # Create superuser
        self.stdout.write('👨‍💼 Creating superuser...')
        superuser, created = User.objects.get_or_create(
            username='admin',
            email='admin@example.com',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        if created:
            superuser.set_password('admin123')
            superuser.save()
            self.stdout.write('  ✓ Created superuser: admin@example.com (pwd: admin123)')
        else:
            self.stdout.write('  ℹ Superuser already exists')

        self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully!'))
        self.stdout.write('\n📊 Summary:')
        self.stdout.write(f'  - Categories: {Category.objects.count()}')
        self.stdout.write(f'  - Authors: {Author.objects.count()}')
        self.stdout.write(f'  - Books: {Book.objects.count()}')
        self.stdout.write(f'  - Users: {User.objects.count()}')
        self.stdout.write(f'  - Reviews: {Review.objects.count()}')
        self.stdout.write(f'  - Borrows: {Borrow.objects.count()}')
        self.stdout.write(f'  - Orders: {Order.objects.count()}')
