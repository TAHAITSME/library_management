from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Author, Book, Category
from apps.orders.models import Order


User = get_user_model()


class ChatbotTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Data Science', description='Analyse de donnees')
        self.author = Author.objects.create(first_name='Martin', last_name='Kleppmann')
        self.book = Book.objects.create(
            title='Designing Data-Intensive Applications',
            slug='designing-data-intensive-applications',
            isbn='9781449373320',
            author=self.author,
            category=self.category,
            description='Systemes de donnees fiables et scalables.',
            price=Decimal('370.00'),
            publication_date='2017-03-16',
            publisher="O'Reilly Media",
            pages=616,
            language='Anglais',
            total_copies=4,
            available_copies=4,
            status='available',
            rating=4.8,
        )
        self.user = User.objects.create_user(username='client', email='client@example.com', password='Pass12345')

    def ask(self, message):
        return self.client.post(
            reverse('chatbot:ask'),
            data={'message': message},
            content_type='application/json',
        )

    def test_catalog_search_returns_books(self):
        response = self.ask('livres Data Science disponibles moins de 400 DH')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("J'ai trouve", payload['answer'])
        self.assertEqual(payload['results'][0]['title'], self.book.title)
        self.assertIn('Voir tous les resultats', [action['label'] for action in payload['actions']])

    def test_business_rule_answer_for_borrowing(self):
        response = self.ask("explique la regle d'emprunt 30 jours")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('30% du prix', payload['answer'])
        self.assertIn("montant d'emprunt est double", payload['answer'])

    def test_personal_orders_need_login_then_return_user_orders(self):
        anonymous_response = self.ask('mes commandes')
        self.assertEqual(anonymous_response.status_code, 200)
        self.assertEqual(anonymous_response.json()['actions'][0]['label'], 'Connexion')

        Order.objects.create(
            user=self.user,
            order_number='ORD-TEST',
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('0.00'),
            tax=Decimal('0.00'),
            discount=Decimal('0.00'),
            total=Decimal('100.00'),
            shipping_address='Adresse test',
        )
        self.client.force_login(self.user)
        response = self.ask('mes commandes')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['title'], 'ORD-TEST')

    def test_understands_typos_and_follow_up_context(self):
        first_response = self.ask('je veux des livr data science dispo')
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.json()['results'][0]['title'], self.book.title)

        second_response = self.ask('moins de 400 dh')
        self.assertEqual(second_response.status_code, 200)
        payload = second_response.json()
        self.assertIn('domaine Data Science', payload['answer'])
        self.assertEqual(payload['results'][0]['title'], self.book.title)

    def test_short_message_asks_for_clarification(self):
        response = self.ask('r')

        self.assertEqual(response.status_code, 200)
        self.assertIn("pas assez", response.json()['answer'])

    def test_payment_question_is_not_confused_with_ai_alias(self):
        response = self.ask('comment faire le paiement stripe')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Parcours paiement commande', response.json()['answer'])
        self.assertEqual(response.json()['results'], [])

    def test_answers_simple_conversation_variants(self):
        response = self.ask('salam cv')

        self.assertEqual(response.status_code, 200)
        self.assertIn('BiblioNUM', response.json()['answer'])

    def test_answers_project_business_question(self):
        response = self.ask('c est quoi le role de cette application bibliotheque')

        self.assertEqual(response.status_code, 200)
        self.assertIn('application de gestion de bibliotheque', response.json()['answer'])

    def test_answers_stock_question_without_blocking_precise_search(self):
        stock_response = self.ask('explique moi le stock des exemplaires')
        self.assertEqual(stock_response.status_code, 200)
        self.assertIn('Le stock indique', stock_response.json()['answer'])

        search_response = self.ask('livres Data Science disponibles moins de 400 DH')
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json()['results'][0]['title'], self.book.title)

    def test_answers_admin_and_security_business_questions(self):
        admin_response = self.ask('que fait administrateur dans le dashboard')
        self.assertEqual(admin_response.status_code, 200)
        self.assertIn('tableau de bord', admin_response.json()['answer'])

        security_response = self.ask('comment proteger les donnees et mot de passe')
        self.assertEqual(security_response.status_code, 200)
        self.assertIn('authentification', security_response.json()['answer'])

    def test_understands_reservation_variants(self):
        variants = [
            'comment reserver un livre',
            'je veux faire une reservation',
            'reserver ouvrage',
            'comment je peux garder un livre',
        ]

        for message in variants:
            response = self.ask(message)
            self.assertEqual(response.status_code, 200)
            self.assertIn('bouton Reserver', response.json()['answer'])

    def test_answers_invoice_stock_and_unknown_helpfully(self):
        invoice_response = self.ask('ou trouver ma facture')
        self.assertEqual(invoice_response.status_code, 200)
        self.assertIn('facture', invoice_response.json()['answer'].lower())

        stock_response = self.ask('livre indisponible et stock')
        self.assertEqual(stock_response.status_code, 200)
        self.assertIn('stock', stock_response.json()['answer'].lower())

        unknown_response = self.ask('xyzqsdplm')
        self.assertEqual(unknown_response.status_code, 200)
        self.assertIn('Je peux vous aider', unknown_response.json()['answer'])

    def test_conversational_intents_and_context_followups(self):
        greeting = self.ask('slt')
        self.assertEqual(greeting.status_code, 200)
        self.assertIn('assistant BiblioNUM', greeting.json()['answer'])

        take_book = self.ask('je veux prendre un livre')
        self.assertEqual(take_book.status_code, 200)
        self.assertIn('emprunter', take_book.json()['answer'].lower())

        reservation = self.ask('faire une reservation')
        self.assertEqual(reservation.status_code, 200)
        self.assertIn('Mes reservations', reservation.json()['answer'])

        unavailable = self.ask("et si le livre n'est pas disponible ?")
        self.assertEqual(unavailable.status_code, 200)
        self.assertIn("file d'attente", unavailable.json()['answer'])

        payment = self.ask('je veux payer')
        self.assertEqual(payment.status_code, 200)
        self.assertIn('Stripe', payment.json()['answer'])

        after_payment = self.ask('et apres le paiement ?')
        self.assertEqual(after_payment.status_code, 200)
        self.assertIn('facture', after_payment.json()['answer'].lower())

    def test_vague_problem_asks_clarification(self):
        response = self.ask('ca ne marche pas')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('Pouvez-vous preciser', payload['answer'])
        self.assertIn('Paiement', payload['suggestions'])
