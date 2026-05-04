from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from urllib.parse import urlparse


class Category(models.Model):
    """Catégorie de livres"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Classe Font Awesome")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
    
    def __str__(self):
        return self.name


class Author(models.Model):
    """Auteur de livre"""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Auteur'
        verbose_name_plural = 'Auteurs'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    """Livre dans le catalogue"""
    
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('unavailable', 'Indisponible'),
        ('discontinued', 'Discontinué'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    isbn = models.CharField(max_length=20, unique=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cover_image = models.ImageField(
        upload_to='books/covers/',
        null=True,
        blank=True,
        help_text='Image de couverture du livre'
    )
    publication_date = models.DateField()
    publisher = models.CharField(max_length=200)
    pages = models.IntegerField(validators=[MinValueValidator(1)])
    language = models.CharField(max_length=50, default='Français')
    
    # Inventaire
    total_copies = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    available_copies = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Évaluation
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    number_of_reviews = models.IntegerField(default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Livre'
        verbose_name_plural = 'Livres'
    
    def __str__(self):
        return self.title
    
    def is_available(self):
        """Vérifier si le livre est disponible"""
        return self.available_copies > 0 and self.status == 'available'

    def get_cover_image_url(self):
        """Retourner une URL exploitable pour les anciennes URLs et les nouveaux uploads."""
        if not self.cover_image:
            return ''

        image_name = str(self.cover_image)
        parsed = urlparse(image_name)
        if parsed.scheme in ('http', 'https'):
            return image_name

        try:
            return self.cover_image.url
        except ValueError:
            return ''


class Review(models.Model):
    """Avis sur un livre"""
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['book', 'user']
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
    
    def __str__(self):
        return f"Avis de {self.user.username} sur {self.book.title} ({self.rating}/5)"
    
    def __str__(self):
        return f"Avis de {self.user} sur {self.book}"


class Wishlist(models.Model):
    """Liste de souhaits utilisateur"""
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Liste de souhaits'
        verbose_name_plural = 'Listes de souhaits'

    def __str__(self):
        return f"Wishlist de {self.user}"

    def get_item_count(self):
        """Nombre de livres dans la wishlist"""
        return self.items.count()


class WishlistItem(models.Model):
    """Article dans la liste de souhaits"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(
        default=0,
        choices=[(0, 'Basse'), (1, 'Normale'), (2, 'Haute')],
        help_text='Niveau de priorité'
    )

    class Meta:
        unique_together = ['wishlist', 'book']
        verbose_name = 'Article wishlist'
        verbose_name_plural = 'Articles wishlist'
        ordering = ['-priority', '-added_at']

    def __str__(self):
        return f"{self.wishlist.user} - {self.book.title}"
