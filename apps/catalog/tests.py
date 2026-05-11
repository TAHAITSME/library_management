from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Author, Book, Category


class CatalogSearchTests(TestCase):
    def setUp(self):
        self.data = Category.objects.create(name='Data Science')
        self.finance = Category.objects.create(name='Finance')
        self.author = Author.objects.create(first_name='Martin', last_name='Kleppmann')
        other_author = Author.objects.create(first_name='Alice', last_name='Durand')

        self.designing_data = Book.objects.create(
            title='Designing Data-Intensive Applications',
            slug='designing-data-intensive-applications',
            isbn='9781449373320',
            author=self.author,
            category=self.data,
            description='Distributed systems and databases.',
            price=Decimal('320.00'),
            publication_date=date(2017, 3, 16),
            publisher="O'Reilly",
            pages=616,
            language='English',
            available_copies=3,
        )
        self.finance_book = Book.objects.create(
            title='Analyse financiere moderne',
            slug='analyse-financiere-moderne',
            isbn='9780000000001',
            author=other_author,
            category=self.finance,
            description='Introduction aux marches et aux ratios financiers.',
            price=Decimal('180.00'),
            publication_date=date(2023, 1, 1),
            publisher='Biblio Press',
            pages=240,
            language='Francais',
            available_copies=2,
        )
        self.description_match = Book.objects.create(
            title='Architecture logicielle',
            slug='architecture-logicielle',
            isbn='9780000000002',
            author=other_author,
            category=self.data,
            description='Un chapitre cite Designing Data-Intensive Applications.',
            price=Decimal('210.00'),
            publication_date=date(2022, 1, 1),
            publisher='Tech Press',
            pages=300,
            language='Francais',
            available_copies=1,
        )

    def test_catalog_search_matches_multi_word_author(self):
        response = self.client.get(reverse('catalog:books_list'), {'q': 'martin kleppmann'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.designing_data.title)
        self.assertNotContains(response, self.finance_book.title)

    def test_catalog_search_matches_category(self):
        response = self.client.get(reverse('catalog:books_list'), {'q': 'finance'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.finance_book.title)
        self.assertNotContains(response, self.designing_data.title)

    def test_short_query_does_not_match_every_book(self):
        response = self.client.get(reverse('catalog:books_list'), {'q': 'z'})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.designing_data.title)
        self.assertNotContains(response, self.finance_book.title)

    def test_search_ajax_returns_json_results(self):
        response = self.client.get(reverse('catalog:search'), {'q': 'data', 'ajax': '1'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        payload = response.json()
        self.assertGreaterEqual(payload['count'], 1)
        self.assertEqual(payload['results'][0]['title'], self.designing_data.title)
        self.assertIn('/catalog/book/', payload['results'][0]['url'])

    def test_relevance_prefers_title_match_over_description_match(self):
        response = self.client.get(reverse('catalog:books_list'), {'q': 'Designing Data'})

        self.assertEqual(response.status_code, 200)
        books = list(response.context['books'])
        self.assertGreaterEqual(len(books), 2)
        self.assertEqual(books[0], self.designing_data)
