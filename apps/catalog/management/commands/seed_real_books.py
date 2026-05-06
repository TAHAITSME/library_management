from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from apps.catalog.models import Author, Book, Category


REAL_BOOKS = [
    {
        "title": "1984",
        "isbn": "9780451524935",
        "author": ("George", "Orwell"),
        "category": "Fiction",
        "description": "Roman dystopique sur la surveillance, la manipulation politique et le controle social.",
        "price": "89.00",
        "publication_date": "1949-06-08",
        "publisher": "Secker & Warburg",
        "pages": 328,
        "language": "Anglais",
        "total_copies": 8,
        "rating": 4.7,
    },
    {
        "title": "Animal Farm",
        "isbn": "9780451526342",
        "author": ("George", "Orwell"),
        "category": "Fiction",
        "description": "Fable politique qui critique les regimes autoritaires a travers une revolte d'animaux.",
        "price": "69.00",
        "publication_date": "1945-08-17",
        "publisher": "Secker & Warburg",
        "pages": 112,
        "language": "Anglais",
        "total_copies": 7,
        "rating": 4.5,
    },
    {
        "title": "Pride and Prejudice",
        "isbn": "9780141439518",
        "author": ("Jane", "Austen"),
        "category": "Romance",
        "description": "Classique de la litterature anglaise sur l'amour, la reputation et les classes sociales.",
        "price": "75.00",
        "publication_date": "1813-01-28",
        "publisher": "T. Egerton",
        "pages": 432,
        "language": "Anglais",
        "total_copies": 6,
        "rating": 4.6,
    },
    {
        "title": "To Kill a Mockingbird",
        "isbn": "9780061120084",
        "author": ("Harper", "Lee"),
        "category": "Fiction",
        "description": "Roman majeur sur la justice, le racisme et l'enfance dans le sud des Etats-Unis.",
        "price": "95.00",
        "publication_date": "1960-07-11",
        "publisher": "J. B. Lippincott & Co.",
        "pages": 336,
        "language": "Anglais",
        "total_copies": 5,
        "rating": 4.8,
    },
    {
        "title": "The Great Gatsby",
        "isbn": "9780743273565",
        "author": ("F. Scott", "Fitzgerald"),
        "category": "Fiction",
        "description": "Portrait du reve americain, de la richesse et des illusions dans les annees 1920.",
        "price": "82.00",
        "publication_date": "1925-04-10",
        "publisher": "Charles Scribner's Sons",
        "pages": 180,
        "language": "Anglais",
        "total_copies": 6,
        "rating": 4.3,
    },
    {
        "title": "The Catcher in the Rye",
        "isbn": "9780316769488",
        "author": ("J. D.", "Salinger"),
        "category": "Fiction",
        "description": "Recit d'adolescence autour de Holden Caulfield, de l'identite et du rejet social.",
        "price": "88.00",
        "publication_date": "1951-07-16",
        "publisher": "Little, Brown and Company",
        "pages": 277,
        "language": "Anglais",
        "total_copies": 4,
        "rating": 4.0,
    },
    {
        "title": "The Hobbit",
        "isbn": "9780547928227",
        "author": ("J. R. R.", "Tolkien"),
        "category": "Fantasy",
        "description": "Aventure de Bilbo Baggins dans la Terre du Milieu, prelude au Seigneur des anneaux.",
        "price": "110.00",
        "publication_date": "1937-09-21",
        "publisher": "George Allen & Unwin",
        "pages": 310,
        "language": "Anglais",
        "total_copies": 7,
        "rating": 4.8,
    },
    {
        "title": "The Fellowship of the Ring",
        "isbn": "9780618574940",
        "author": ("J. R. R.", "Tolkien"),
        "category": "Fantasy",
        "description": "Premier volume du Seigneur des anneaux, centre sur la communaute chargee de detruire l'Anneau.",
        "price": "125.00",
        "publication_date": "1954-07-29",
        "publisher": "George Allen & Unwin",
        "pages": 423,
        "language": "Anglais",
        "total_copies": 5,
        "rating": 4.9,
    },
    {
        "title": "Dune",
        "isbn": "9780441172719",
        "author": ("Frank", "Herbert"),
        "category": "Science Fiction",
        "description": "Roman de science-fiction sur la politique, l'ecologie et le pouvoir sur la planete Arrakis.",
        "price": "130.00",
        "publication_date": "1965-08-01",
        "publisher": "Chilton Books",
        "pages": 412,
        "language": "Anglais",
        "total_copies": 6,
        "rating": 4.7,
    },
    {
        "title": "Foundation",
        "isbn": "9780553293357",
        "author": ("Isaac", "Asimov"),
        "category": "Science Fiction",
        "description": "Cycle fondateur de la science-fiction autour de la psychohistoire et de la chute d'un empire galactique.",
        "price": "105.00",
        "publication_date": "1951-06-01",
        "publisher": "Gnome Press",
        "pages": 255,
        "language": "Anglais",
        "total_copies": 5,
        "rating": 4.6,
    },
    {
        "title": "Fahrenheit 451",
        "isbn": "9781451673319",
        "author": ("Ray", "Bradbury"),
        "category": "Science Fiction",
        "description": "Roman dystopique sur la censure, les livres interdits et la liberte de penser.",
        "price": "90.00",
        "publication_date": "1953-10-19",
        "publisher": "Ballantine Books",
        "pages": 249,
        "language": "Anglais",
        "total_copies": 5,
        "rating": 4.4,
    },
    {
        "title": "Brave New World",
        "isbn": "9780060850524",
        "author": ("Aldous", "Huxley"),
        "category": "Science Fiction",
        "description": "Anticipation sociale sur le conditionnement, le bonheur impose et la perte de liberte.",
        "price": "92.00",
        "publication_date": "1932-01-01",
        "publisher": "Chatto & Windus",
        "pages": 288,
        "language": "Anglais",
        "total_copies": 5,
        "rating": 4.4,
    },
    {
        "title": "The Alchemist",
        "isbn": "9780061122415",
        "author": ("Paulo", "Coelho"),
        "category": "Developpement personnel",
        "description": "Conte philosophique sur la quete personnelle, les signes et la realisation de son reve.",
        "price": "85.00",
        "publication_date": "1988-01-01",
        "publisher": "HarperOne",
        "pages": 208,
        "language": "Anglais",
        "total_copies": 8,
        "rating": 4.2,
    },
    {
        "title": "Sapiens: A Brief History of Humankind",
        "isbn": "9780062316097",
        "author": ("Yuval Noah", "Harari"),
        "category": "Histoire",
        "description": "Synthese historique sur l'evolution de l'humanite, des chasseurs-cueilleurs aux societes modernes.",
        "price": "155.00",
        "publication_date": "2011-01-01",
        "publisher": "Harvill Secker",
        "pages": 443,
        "language": "Anglais",
        "total_copies": 6,
        "rating": 4.6,
    },
    {
        "title": "A Brief History of Time",
        "isbn": "9780553380163",
        "author": ("Stephen", "Hawking"),
        "category": "Science",
        "description": "Introduction accessible aux trous noirs, au Big Bang et aux grandes questions de la cosmologie.",
        "price": "120.00",
        "publication_date": "1988-04-01",
        "publisher": "Bantam Books",
        "pages": 212,
        "language": "Anglais",
        "total_copies": 5,
        "rating": 4.5,
    },
    {
        "title": "Cosmos",
        "isbn": "9780345539434",
        "author": ("Carl", "Sagan"),
        "category": "Science",
        "description": "Voyage scientifique et philosophique a travers l'univers, l'histoire des sciences et la place de l'humanite.",
        "price": "135.00",
        "publication_date": "1980-01-01",
        "publisher": "Random House",
        "pages": 384,
        "language": "Anglais",
        "total_copies": 4,
        "rating": 4.7,
    },
    {
        "title": "Clean Code",
        "isbn": "9780132350884",
        "author": ("Robert C.", "Martin"),
        "category": "Informatique",
        "description": "Reference pratique sur l'ecriture d'un code lisible, maintenable et professionnel.",
        "price": "210.00",
        "publication_date": "2008-08-01",
        "publisher": "Prentice Hall",
        "pages": 464,
        "language": "Anglais",
        "total_copies": 4,
        "rating": 4.7,
    },
    {
        "title": "Introduction to Algorithms",
        "isbn": "9780262046305",
        "author": ("Thomas H.", "Cormen"),
        "category": "Informatique",
        "description": "Ouvrage de reference sur les algorithmes, les structures de donnees et l'analyse de complexite.",
        "price": "390.00",
        "publication_date": "2022-04-05",
        "publisher": "MIT Press",
        "pages": 1312,
        "language": "Anglais",
        "total_copies": 3,
        "rating": 4.6,
    },
    {
        "title": "The Pragmatic Programmer",
        "isbn": "9780135957059",
        "author": ("David", "Thomas"),
        "category": "Informatique",
        "description": "Guide professionnel sur les bonnes pratiques, la conception et l'attitude du developpeur pragmatique.",
        "price": "260.00",
        "publication_date": "2019-09-13",
        "publisher": "Addison-Wesley Professional",
        "pages": 352,
        "language": "Anglais",
        "total_copies": 4,
        "rating": 4.8,
    },
    {
        "title": "Design Patterns",
        "isbn": "9780201633610",
        "author": ("Erich", "Gamma"),
        "category": "Informatique",
        "description": "Catalogue classique de patrons de conception pour la programmation orientee objet.",
        "price": "300.00",
        "publication_date": "1994-10-31",
        "publisher": "Addison-Wesley Professional",
        "pages": 395,
        "language": "Anglais",
        "total_copies": 3,
        "rating": 4.5,
    },
]


CATEGORY_DATA = {
    "Fiction": ("Romans classiques et litterature generale.", "fas fa-book"),
    "Romance": ("Romans centres sur les relations et les sentiments.", "fas fa-heart"),
    "Fantasy": ("Univers imaginaires, magie et aventures epique.", "fas fa-hat-wizard"),
    "Science Fiction": ("Futurs possibles, technologies et mondes imaginaires.", "fas fa-rocket"),
    "Developpement personnel": ("Livres de reflexion personnelle et d'inspiration.", "fas fa-seedling"),
    "Histoire": ("Ouvrages historiques et analyses de civilisation.", "fas fa-landmark"),
    "Science": ("Vulgarisation scientifique et connaissances generales.", "fas fa-atom"),
    "Informatique": ("Programmation, algorithmique et genie logiciel.", "fas fa-laptop-code"),
}


AUTHOR_DATA = {
    ("George", "Orwell"): {
        "birth_date": "1903-06-25",
        "nationality": "Britannique",
        "website": "https://www.orwellfoundation.com/",
    },
    ("Jane", "Austen"): {
        "birth_date": "1775-12-16",
        "nationality": "Britannique",
        "website": "https://janeaustens.house/",
    },
    ("Harper", "Lee"): {"birth_date": "1926-04-28", "nationality": "Americaine"},
    ("F. Scott", "Fitzgerald"): {"birth_date": "1896-09-24", "nationality": "Americain"},
    ("J. D.", "Salinger"): {"birth_date": "1919-01-01", "nationality": "Americain"},
    ("J. R. R.", "Tolkien"): {"birth_date": "1892-01-03", "nationality": "Britannique"},
    ("Frank", "Herbert"): {"birth_date": "1920-10-08", "nationality": "Americain"},
    ("Isaac", "Asimov"): {"birth_date": "1920-01-02", "nationality": "Americain"},
    ("Ray", "Bradbury"): {"birth_date": "1920-08-22", "nationality": "Americain"},
    ("Aldous", "Huxley"): {"birth_date": "1894-07-26", "nationality": "Britannique"},
    ("Paulo", "Coelho"): {"birth_date": "1947-08-24", "nationality": "Bresilien"},
    ("Yuval Noah", "Harari"): {"birth_date": "1976-02-24", "nationality": "Israelien"},
    ("Stephen", "Hawking"): {"birth_date": "1942-01-08", "nationality": "Britannique"},
    ("Carl", "Sagan"): {"birth_date": "1934-11-09", "nationality": "Americain"},
    ("Robert C.", "Martin"): {"birth_date": "1952-12-05", "nationality": "Americain"},
    ("Thomas H.", "Cormen"): {"birth_date": "1956-01-01", "nationality": "Americain"},
    ("David", "Thomas"): {"birth_date": "1956-01-01", "nationality": "Americain"},
    ("Erich", "Gamma"): {"birth_date": "1961-03-13", "nationality": "Suisse"},
}


class Command(BaseCommand):
    help = "Add real books, authors, categories and cover images to the catalog."

    def handle(self, *args, **options):
        created_books = 0
        updated_books = 0

        with transaction.atomic():
            categories = self.create_categories()
            authors = self.create_authors()

            for item in REAL_BOOKS:
                book, created = self.upsert_book(item, authors, categories)
                if created:
                    created_books += 1
                    self.stdout.write(f"Created: {book.title}")
                else:
                    updated_books += 1
                    self.stdout.write(f"Updated: {book.title}")

        self.stdout.write(self.style.SUCCESS("Real book data imported successfully."))
        self.stdout.write(f"Created books: {created_books}")
        self.stdout.write(f"Updated books: {updated_books}")
        self.stdout.write(f"Total books in catalog: {Book.objects.count()}")

    def create_categories(self):
        categories = {}
        for name, (description, icon) in CATEGORY_DATA.items():
            category, _ = Category.objects.update_or_create(
                name=name,
                defaults={"description": description, "icon": icon},
            )
            categories[name] = category
        return categories

    def create_authors(self):
        authors = {}
        for name, defaults in AUTHOR_DATA.items():
            first_name, last_name = name
            author, _ = Author.objects.update_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults=defaults,
            )
            authors[name] = author
        return authors

    def upsert_book(self, item, authors, categories):
        author = authors[item["author"]]
        category = categories[item["category"]]
        cover_url = f"https://covers.openlibrary.org/b/isbn/{item['isbn']}-L.jpg"

        defaults = {
            "title": item["title"],
            "slug": self.unique_slug(item["title"], item["isbn"]),
            "author": author,
            "category": category,
            "description": item["description"],
            "price": Decimal(item["price"]),
            "cover_image": cover_url,
            "publication_date": item["publication_date"],
            "publisher": item["publisher"],
            "pages": item["pages"],
            "language": item["language"],
            "total_copies": item["total_copies"],
            "available_copies": item["total_copies"],
            "status": "available",
            "rating": item["rating"],
            "number_of_reviews": 0,
        }

        book = Book.objects.filter(isbn=item["isbn"]).first()
        if book is None:
            book = Book.objects.filter(title=item["title"]).first()

        if book is not None:
            for field, value in defaults.items():
                setattr(book, field, value)
            book.isbn = item["isbn"]
            book.save()
            return book, False

        try:
            return Book.objects.create(isbn=item["isbn"], **defaults), True
        except IntegrityError:
            defaults["slug"] = self.unique_slug(item["title"], item["isbn"], force_suffix=True)
            return Book.objects.create(isbn=item["isbn"], **defaults), True

    def unique_slug(self, title, isbn, force_suffix=False):
        base_slug = slugify(title)[:42] or "book"
        slug = base_slug if not force_suffix else f"{base_slug}-{isbn[-4:]}"

        if not Book.objects.filter(slug=slug).exists():
            return slug

        candidate = f"{base_slug}-{isbn[-4:]}"
        if not Book.objects.filter(slug=candidate).exists():
            return candidate

        counter = 2
        while Book.objects.filter(slug=f"{candidate}-{counter}").exists():
            counter += 1
        return f"{candidate}-{counter}"
